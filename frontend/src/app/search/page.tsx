"use client";

import { FormEvent, useCallback, useState } from "react";
import { FeedItem, searchFeed } from "../../lib/api";
import { getUserId } from "../../lib/user";
import ShortFormSection from "../../components/feed/ShortFormSection";

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [items, setItems] = useState<FeedItem[] | null>(null);

  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const runSearch = useCallback(async (cursor: string | null) => {
    const uid = getUserId();
    if (!uid) return;

    const out = await searchFeed(uid, q.trim(), 20, cursor);

    setItems((prev) => (cursor ? [...(prev ?? []), ...(out.items ?? [])] : out.items ?? []));
    setNextCursor(out.next_cursor ?? null);
    setHasMore(Boolean(out.has_more));
  }, [q]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;

    setLoading(true);
    setErr(null);

    try {
      await runSearch(null);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  const fetchMore = useCallback(async () => {
    if (!hasMore || loadingMore || !nextCursor) return;
    setLoadingMore(true);
    try {
      await runSearch(nextCursor);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, nextCursor, runSearch]);

  // 처음엔 검색창만
  if (items === null) {
    return (
      <div style={{ padding: 24, display: "grid", placeItems: "center", minHeight: "70dvh" }}>
        <div
          style={{
            width: "min(720px, 100%)",
            padding: 20,
            borderRadius: 20,
            background: "rgba(255,255,255,0.9)",
            border: "1px solid rgba(17, 18, 24, 0.08)",
            boxShadow: "0 18px 50px rgba(17, 18, 24, 0.16)",
            backdropFilter: "blur(12px)",
          }}
        >
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", color: "#111218" }}>
            Quick Search
          </div>
          <form onSubmit={onSubmit} style={{ marginTop: 14, display: "flex", gap: 10 }}>
            <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="검색어를 입력하세요 (예: RAG, retrieval, diffusion...)"
              style={{
                flex: 1,
                padding: "12px 14px",
                border: "1px solid rgba(17, 18, 24, 0.12)",
                borderRadius: 14,
                background: "white",
                fontSize: 14,
                color: "#111218",
              }}
            />
            <button
            disabled={loading}
            style={{
              padding: "12px 16px",
              borderRadius: 14,
              border: "1px solid rgba(255, 107, 0, 0.4)",
              background: "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)",
              color: "white",
              fontWeight: 700,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "검색중" : "검색"}
            </button>
          </form>
        </div>
        {err && <div style={{ marginTop: 12, color: "crimson" }}>{err}</div>}
      </div>
    );
  }

  // ✅ 검색 후엔 recommend와 동일 UI
  return (
    <>
      <ShortFormSection items={items} onNeedMore={fetchMore} />
      {loadingMore && <div style={{ padding: 12, opacity: 0.6 }}>다음 검색 결과 불러오는 중...</div>}
      {err && <div style={{ padding: 12, color: "crimson" }}>{err}</div>}
    </>
  );
}
