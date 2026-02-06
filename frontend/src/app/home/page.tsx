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

    const t0 = performance.now();
    const out = await getFeed(uid, 20, cursor, m === "smart" ? "smart" : "fast");
    const t1 = performance.now();
    console.log(`[feed] mode=${m} loaded in ${Math.round(t1 - t0)}ms`);

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

  // 로딩 중 화면
  if (loading) {
    return (
      <div style={{
        position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh",
        display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center",
        background: "#ffffff", zIndex: 1000
      }}>
        <div style={{ fontSize: "60px", marginBottom: "20px" }}>🐣</div> 
        <div style={{ fontSize: "20px", fontWeight: "700", color: "#111218" }}>
          {mode === "smart" ? (
            <>논문을 꼼꼼하게 분석하는 중이에요</>
          ) : (
            <>사용자님께 딱 맞는 논문을 가져오고 있어요</>
          )}
        </div>
        <div style={{ marginTop: "10px", fontSize: "14px", color: "#64748b" }}>
          {mode === "smart" ? (
            <>스마트 모드는 정교한 결과를 위해 응답이 느릴 수 있어요</>
          ) : (
            <>잠시만 기다려 주세요.</>
          )}
        </div>
      </div>
    );
  }

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
      {!loading && <ShortFormSection items={items} onNeedMore={fetchMore} />}
      {mode === "fast" && loadingMore && (
        <div style={{ padding: 12, opacity: 0.6 }}></div>
      )}
      {mode === "smart" && (
        <div style={{ padding: 12, opacity: 0.6 }}></div>
      )}
    </>
  );
}
