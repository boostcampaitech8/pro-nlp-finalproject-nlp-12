"use client";

import { useEffect, useState, use } from "react";
import { getPaperSummary, SummaryItem } from "@/lib/api";
import { getUserId } from "@/lib/user";

export default function PaperDetailPage(props: {
  params: Promise<{ paper_id: string }>;
  searchParams?: Promise<{
    paper_id?: string;
    arxiv_id?: string
  }>;
}) {
  const searchParams = props.searchParams ? use(props.searchParams) : {};

  const paper_id = searchParams.paper_id;
  const arxiv_id = searchParams.arxiv_id;

  const [paperData, setPaperData] = useState<SummaryItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSummary() {
      const uid = getUserId();
      if (!uid) return;
      try {
        setLoading(true);

        /**
         * [수정] 
         * 1. Smart 모드일 때는 쿼리의 arxiv_id를 우선 사용
         * 2. Fast 모드이거나 일반적인 경우 paper_id를 숫자로 변환하여 사용
         */
        const pid = paper_id ? Number(paper_id) : null;
        const aid = arxiv_id || null;

        const response = await getPaperSummary(uid, pid, aid);
        setPaperData(response);
      } catch (err) {
        console.error("요약본 로드 실패:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSummary();
  }, [paper_id, arxiv_id]);

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
          논문을 열심히 요약하고 있어요!
        </div>
        <div style={{ marginTop: "10px", fontSize: "14px", color: "#64748b" }}>
          잠시만 기다려 주세요...
        </div>
      </div>
    );
  }

  // 준비 된 요약 결과가 없을 때의 화면
  if (!loading && (!paperData?.summaries || paperData?.summaries.length == 0)) {
    return (
      <div style={{
        position: "fixed", top: 0, left: 0, width: "100vw", height: "100vh",
        display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center",
        background: "#ffffff", zIndex: 1000
      }}>
        <div style={{ fontSize: "60px", marginBottom: "20px" }}>📭</div> 
        <div style={{ fontSize: "20px", fontWeight: "700", color: "#111218" }}>
          준비된 요약 내용이 없습니다.
        </div>
      </div>
    );
  }

  // 특정 타입의 요약을 찾는 함수
  const getSummary = (type: string) =>
    paperData?.summaries.find(s => s.summary_type.toLowerCase() === type.toLowerCase())?.summary_text;

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: "24px 16px 120px" }}>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <div style={{ marginTop: 20, display: "grid", gap: 16 }}>
          <SummaryBox title="Motivation" text={getSummary("motivation")} color="rgba(255, 107, 0, 0.08)" borderColor="rgba(255, 107, 0, 0.2)" />
          <SummaryBox title="Methodology" text={getSummary("methodology")} color="rgba(0, 194, 168, 0.08)" borderColor="rgba(0, 194, 168, 0.2)" />
          <SummaryBox title="Performance" text={getSummary("performance")} color="rgba(17, 18, 24, 0.04)" borderColor="rgba(17, 18, 24, 0.08)" />
          <SummaryBox title="Significance" text={getSummary("significance")} color="rgba(255, 45, 85, 0.08)" borderColor="rgba(255, 45, 85, 0.2)" />
        </div>

        <div style={{ marginTop: 18, display: "flex", gap: 10, flexWrap: "wrap" }}>
          {paperData?.abs_url ? (
            <a
              href={paperData?.abs_url}
              target="_blank"
              rel="noreferrer"
              style={{
                padding: "10px 14px",
                borderRadius: 12,
                border: "1px solid rgba(17, 18, 24, 0.12)",
                background: "white",
                fontWeight: 700,
                color: "#111218",
                boxShadow: "0 8px 18px rgba(17, 18, 24, 0.08)",
              }}
            >
              웹 링크
            </a>
          ) : null}
          {paperData?.pdf_url ? (
            <a
              href={paperData?.pdf_url}
              target="_blank"
              rel="noreferrer"
              style={{
                padding: "10px 14px",
                borderRadius: 12,
                border: "1px solid rgba(255, 107, 0, 0.35)",
                background: "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)",
                fontWeight: 700,
                color: "white",
                boxShadow: "0 10px 22px rgba(255, 107, 0, 0.25)",
              }}
            >
              PDF 링크
            </a>
          ) : null}
        </div>
      </div> 
    </div>
  );
}

function SummaryBox({ title, text, color, borderColor }: any) {
  return (
    <div style={{ padding: 20, borderRadius: 18, background: color, border: `1px solid ${borderColor}` }}>
      <div style={{ fontWeight: 800, marginBottom: 8, fontSize: 16 }}>{title}</div>
      <div style={{ fontSize: 15, lineHeight: 1.7, color: "#2c2f3a" }}>
        {text || `${title}에 대한 요약 정보를 찾을 수 없습니다.`}
      </div>
    </div>
  );
}