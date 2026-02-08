"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  const [showModeHelp, setShowModeHelp] = useState(false);
  const helpWrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!showModeHelp) return;

    const onDocClick = (e: MouseEvent) => {
      const target = e.target as Node | null;
      if (!target) return;
      if (helpWrapRef.current && !helpWrapRef.current.contains(target)) {
        setShowModeHelp(false);
      }
    };

    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [showModeHelp]);

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

  return (
    <>
      <div style={{ padding: "12px 16px 0", display: "flex", justifyContent: "center" }}>
        <div
          ref={helpWrapRef}
          style={{ display: "inline-flex", alignItems: "center", gap: 8, position: "relative" }}
        >
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
          <button
            type="button"
            onClick={() => setShowModeHelp((v) => !v)}
            aria-label="추천 모드 안내"
            style={{
              width: 20,
              height: 20,
              borderRadius: 999,
              border: "1px solid rgba(17, 18, 24, 0.18)",
              background: "white",
              fontSize: 12,
              fontWeight: 700,
              color: "#111218",
              lineHeight: "18px",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            i
          </button>
          {showModeHelp && (
            <div
              style={{
                position: "absolute",
                top: 32,
                right: 0,
                width: 240,
                padding: "10px 12px",
                borderRadius: 12,
                background: "white",
                border: "1px solid rgba(17, 18, 24, 0.12)",
                boxShadow: "0 8px 24px rgba(0, 0, 0, 0.08)",
                fontSize: 12,
                color: "#111218",
                zIndex: 5,
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Fast</div>
              <div style={{ color: "#475569", lineHeight: 1.5 }}>
                빠르게 추천을 받아보세요.
                <br />
                저장된 논문을 기반으로 즉시 보여줍니다.
              </div>
              <div style={{ fontWeight: 700, margin: "10px 0 6px" }}>Smart</div>
              <div style={{ color: "#475569", lineHeight: 1.5 }}>
                더 넓게 탐색합니다.
                <br />
                실시간으로 논문을 확장 탐색하여
                <br />
                더 다양한 추천을 제공합니다.
                <br />
                (조금 더 시간이 걸릴 수 있어요)
              </div>
            </div>
          )}
        </div>
      </div>
      {loading && (
        <div
          style={{
            padding: "12px 16px",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            minHeight: "42dvh",
          }}
        >
          <div
            style={{
              width: "min(640px, 100%)",
              padding: "22px 18px 18px",
              borderRadius: 16,
              border: "1px solid rgba(17, 18, 24, 0.08)",
              background: "rgba(255, 255, 255, 0.9)",
              boxShadow: "0 10px 30px rgba(17, 18, 24, 0.12)",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              gap: 10,
            }}
          >
            <div style={{ fontSize: "34px", lineHeight: 1 }}>🐣</div>
            <div>
              <div style={{ fontSize: "16px", fontWeight: 700, color: "#111218" }}>
                {mode === "smart" ? (
                  <>논문을 꼼꼼하게 분석하는 중이에요</>
                ) : (
                  <>사용자님께 딱 맞는 논문을 가져오고 있어요</>
                )}
              </div>
              <div style={{ marginTop: 6, fontSize: "13px", color: "#64748b" }}>
                {mode === "smart" ? (
                  <>스마트 모드는 정교한 결과를 위해 응답이 느릴 수 있어요</>
                ) : (
                  <>잠시만 기다려 주세요.</>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      {!loading && <ShortFormSection items={items} onNeedMore={fetchMore} mode={mode} />}
      {mode === "fast" && loadingMore && <div style={{ padding: 12, opacity: 0.6 }}></div>}
      {mode === "smart" && <div style={{ padding: 12, opacity: 0.6 }}></div>}
    </>
  );
}
