"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { FeedItem, postEvent } from "../../lib/api";
import { getUserId } from "../../lib/user";
import { useLibraryState } from "../common/useLibraryState";

type PendingKey = `${number}:${"like" | "bookmark"}`;

export default function ShortFormSection({
  items,
  onNeedMore,
}: {
  items: FeedItem[];
  onNeedMore?: () => void;
}) {
  const userId = getUserId()!;
  const { isActive, toggle, loading: libLoading, err: libErr } = useLibraryState(userId);

  const [idx, setIdx] = useState(0);
  const [pending, setPending] = useState<Set<PendingKey>>(new Set());
  const [toast, setToast] = useState<string | null>(null);

  const impressedRef = useRef<Set<number>>(new Set());

  // 10초 자동 넘김
  useEffect(() => {
    if (!items?.length) return;
    const t = setInterval(() => setIdx((v) => (v + 1) % items.length), 10_000);
    return () => clearInterval(t);
  }, [items]);

  useEffect(() => {
    if (idx >= (items?.length ?? 0)) setIdx(0);
  }, [idx, items?.length]);

  const cur = useMemo(() => items?.[idx], [items, idx]);

  useEffect(() => {
    if (!cur?.paper_id) return;

    if (impressedRef.current.has(cur.paper_id)) return;
    impressedRef.current.add(cur.paper_id);

    postEvent({
      user_id: userId,
      paper_id: cur.paper_id,
      event_type: "impression",
    }).catch(console.error);
  }, [cur?.paper_id, userId]);

  useEffect(() => {
    if (!onNeedMore) return;
    if (!items?.length) return;

    // 남은 카드 5개 이하이면 다음 페이지를 미리 받아둠
    if (items.length - 1 - idx <= 5) {
      onNeedMore();
    }
  }, [idx, items?.length, onNeedMore]);

  async function onToggle(kind: "like" | "bookmark") {
    if (!cur) return;
    const key: PendingKey = `${cur.paper_id}:${kind}`;

    if (pending.has(key)) return; // 중복 클릭 방지
    setPending((prev) => new Set(prev).add(key));

    try {
      const active = await toggle(cur.paper_id, kind);
      setToast(active ? `${kind} ON` : `${kind} OFF`);
      window.setTimeout(() => setToast(null), 800);
    } catch (e: any) {
      setToast("네트워크 오류로 되돌렸어");
      window.setTimeout(() => setToast(null), 1200);
      console.error(e);
    } finally {
      setPending((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  }

  if (!cur) return <div style={{ padding: 16 }}>표시할 논문이 없습니다.</div>;

  const liked = isActive(cur.paper_id, "like");
  const bookmarked = isActive(cur.paper_id, "bookmark");

  const likeKey: PendingKey = `${cur.paper_id}:like`;
  const bmKey: PendingKey = `${cur.paper_id}:bookmark`;

  const likeDisabled = pending.has(likeKey);
  const bmDisabled = pending.has(bmKey);

  return (
    <section style={{ padding: 16 }}>
      {libLoading && <div style={{ fontSize: 12, opacity: 0.6 }}>내 라이브러리 불러오는 중...</div>}
      {libErr && <div style={{ fontSize: 12, color: "crimson" }}>{libErr}</div>}

      {toast && (
        <div
          style={{
            position: "fixed",
            left: "50%",
            transform: "translateX(-50%)",
            bottom: 80,
            background: "rgba(0,0,0,0.8)",
            color: "white",
            padding: "8px 12px",
            borderRadius: 999,
            fontSize: 12,
          }}
        >
          {toast}
        </div>
      )}

      <div style={{ marginBottom: 12, fontWeight: 800, fontSize: 18 }}>{cur.title}</div>
      <div style={{ opacity: 0.85, lineHeight: 1.5 }}>{cur.abstract}</div>

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <button
          onClick={() => onToggle("like")}
          disabled={likeDisabled}
          aria-pressed={liked}
          style={{
            padding: "10px 12px",
            borderRadius: 12,
            border: "1px solid #ddd",
            opacity: likeDisabled ? 0.6 : 1,
            fontWeight: 700,
          }}
        >
          {liked ? "❤️ Liked" : "🤍 Like"}
        </button>

        <button
          onClick={() => onToggle("bookmark")}
          disabled={bmDisabled}
          aria-pressed={bookmarked}
          style={{
            padding: "10px 12px",
            borderRadius: 12,
            border: "1px solid #ddd",
            opacity: bmDisabled ? 0.6 : 1,
            fontWeight: 700,
          }}
        >
          {bookmarked ? "🔖 Bookmarked" : "📑 Bookmark"}
        </button>
      </div>
    </section>
  );
}
