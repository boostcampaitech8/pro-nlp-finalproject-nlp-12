"use client";

import { useCallback, useEffect, useState } from "react";
import { getFeed, FeedItem } from "../../lib/api";
import { getUserId } from "../../lib/user";
import ShortFormSection from "../../components/feed/ShortFormSection";

export default function HomePage() {
  const [mode, setMode] = useState<"fast" | "smart">("fast");
  const [items, setItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const fetchPage = useCallback(async (cursor: string | null, m: "fast" | "smart") => {
    const uid = getUserId();
    if (!uid) return;

    const out = await getFeed(uid, 20, cursor, m === "smart" ? "smart" : "fast");

    setItems((prev) => (cursor ? [...prev, ...(out.items ?? [])] : out.items ?? []));
    setNextCursor(out.next_cursor ?? null);
    setHasMore(Boolean(out.has_more));
  }, []);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setItems([]);
        setNextCursor(null);
        setHasMore(false);
        await fetchPage(null, mode);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      } finally {
        setLoading(false);
      }
    })();
  }, [fetchPage, mode]);

  const fetchMore = useCallback(async () => {
    if (!hasMore || loadingMore || !nextCursor) return;

    setLoadingMore(true);
    try {
        await fetchPage(nextCursor, mode);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      } finally {
        setLoadingMore(false);
      }
  }, [hasMore, loadingMore, nextCursor, fetchPage, mode]);

  if (err) return <div style={{ padding: 16 }}>에러: {err}</div>;

  return (
    <>
      <div style={{ padding: "12px 16px 0", display: "flex", justifyContent: "center" }}>
        <div
          style={{
            display: "inline-flex",
            gap: 6,
            padding: 4,
            borderRadius: 999,
            border: "1px solid rgba(17, 18, 24, 0.12)",
            background: "white",
          }}
        >
          <button
            onClick={() => setMode("fast")}
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              border: "1px solid transparent",
              background: mode === "fast" ? "rgba(255, 107, 0, 0.16)" : "transparent",
              fontWeight: 700,
              cursor: "pointer",
              color: "#111218",
              fontSize: 12,
            }}
          >
            Fast
          </button>
          <button
            onClick={() => setMode("smart")}
            style={{
              padding: "4px 10px",
              borderRadius: 999,
              border: "1px solid transparent",
              background: mode === "smart" ? "rgba(37, 99, 235, 0.16)" : "transparent",
              fontWeight: 700,
              cursor: "pointer",
              color: "#111218",
              fontSize: 12,
            }}
          >
            Smart
          </button>
        </div>
      </div>
      {loading && (
        <div style={{ padding: "10px 16px 0", color: "#0f172a", fontWeight: 700, textAlign: "center" }}>
          추천을 불러오는 중...
        </div>
      )}
      {!loading && <ShortFormSection items={items} onNeedMore={fetchMore} />}
      {mode === "fast" && loadingMore && (
        <div style={{ padding: 12, opacity: 0.6 }}>다음 추천 불러오는 중...</div>
      )}
      {mode === "smart" && (
        <div style={{ padding: 12, opacity: 0.6 }}>
          Smart 모드는 분석 기반 추천입니다. (응답이 느릴 수 있어요)
        </div>
      )}
    </>
  );
}
