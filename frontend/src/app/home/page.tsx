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
  const [err, setErr] = useState<string | null>(null);

  const fetchPage = useCallback(async (cursor: string | null) => {
    const uid = getUserId();
    if (!uid) return;

    const out = await getFeed(uid, 20, cursor);

    setItems((prev) => (cursor ? [...prev, ...(out.items ?? [])] : out.items ?? []));
    setNextCursor(out.next_cursor ?? null);
    setHasMore(Boolean(out.has_more));
  }, []);

  const mockSmartItems: FeedItem[] = [
    {
      paper_id: 1000001,
      title: "LLM + arXiv Live Blend: 최신 키워드 맵 기반 추천",
      abstract:
        "실시간 arXiv 메타와 LLM 요약을 결합해 최근 트렌드/관심 분야를 넓게 탐색할 수 있도록 구성된 피드입니다.",
      primary_category: "cs.CL",
      published_at: "2026-02-04",
    },
    {
      paper_id: 1000002,
      title: "교차 분야 탐색 추천: CV · NLP · RL",
      abstract:
        "학제 간 연결 고리를 강조해 빠르게 분야를 넘나드는 탐색이 가능한 추천 흐름을 보여줍니다.",
      primary_category: "cs.LG",
      published_at: "2026-02-03",
    },
    {
      paper_id: 1000003,
      title: "산업 트렌드 스냅샷: 채용 연관 키워드 중심 요약",
      abstract:
        "취업/포트폴리오 관점에서 유의미한 키워드를 중심으로 논문을 요약해 보여주는 샘플입니다.",
      primary_category: "cs.AI",
      published_at: "2026-02-02",
    },
  ];

  useEffect(() => {
    if (mode === "smart") {
      setItems(mockSmartItems);
      setHasMore(false);
      setNextCursor(null);
      return;
    }

    (async () => {
      try {
        await fetchPage(null);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      }
    })();
  }, [fetchPage, mode]);

  const fetchMore = useCallback(async () => {
    if (!hasMore || loadingMore || !nextCursor) return;

    setLoadingMore(true);
    try {
      await fetchPage(nextCursor);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, nextCursor, fetchPage]);

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
      <ShortFormSection items={items} onNeedMore={fetchMore} />
      {mode === "fast" && loadingMore && (
        <div style={{ padding: 12, opacity: 0.6 }}>다음 추천 불러오는 중...</div>
      )}
      {mode === "smart" && (
        <div style={{ padding: 12, opacity: 0.6 }}>
          Smart 모드는 추후 LLM + arXiv 연동 예정입니다. (현재는 샘플 피드)
        </div>
      )}
    </>
  );
}
