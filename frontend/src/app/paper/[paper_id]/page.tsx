"use client";

import { useEffect, useState, use } from "react";
import { getPaperSummary, SummaryItem } from "@/lib/api";
import { getUserId } from "@/lib/user";

export default function PaperDetailPage(props: {
  params: Promise<{ paper_id: string }>;
  searchParams?: Promise<{ from?: string }>;
}) {
  const params = use(props.params);
  const searchParams = props.searchParams ? use(props.searchParams) : {};
  const paper_id = params.paper_id;

  const [summaries, setSummaries] = useState<SummaryItem[]>([]);
  const [paperData, setPaperData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const backHref = searchParams?.from === "mypage" ? "/mypage" : "/home";

  useEffect(() => {
    async function loadSummary() {
      const uid = getUserId();
      if (!uid) return;
      try {
        setLoading(true);

        // [수정 필요] 요약본과 논문 상세 정보를 동시에 가져오기
        const SummaryData = await getPaperSummary(uid, Number(paper_id));
        setSummaries(SummaryData);
      } catch (err) {
        console.error("요약본 로드 실패:", err);
      } finally {
        setLoading(false);
      }
    }
    loadSummary();
  }, [paper_id]);

  // 특정 타입의 요약을 찾는 함수
  const getSummary = (type: string) =>
    summaries.find(s => s.summary_type.toLowerCase() === type.toLowerCase())?.summary_text;

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: "24px 16px 120px" }}>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <div style={{ marginTop: 20, display: "grid", gap: 16 }}>
          <SummaryBox title="Motivation" text={getSummary("motivation")} color="rgba(255, 107, 0, 0.08)" borderColor="rgba(255, 107, 0, 0.2)" />
          <SummaryBox title="Methodology" text={getSummary("methodology")} color="rgba(0, 194, 168, 0.08)" borderColor="rgba(0, 194, 168, 0.2)" />
          <SummaryBox title="Performance" text={getSummary("performance")} color="rgba(17, 18, 24, 0.04)" borderColor="rgba(17, 18, 24, 0.08)" />
          <SummaryBox title="Significance" text={getSummary("significance")} color="rgba(255, 45, 85, 0.08)" borderColor="rgba(255, 45, 85, 0.2)" />
        </div>

        {/* <div style={{ marginTop: 18, display: "flex", gap: 10, flexWrap: "wrap" }}>
          {paperData.web_url ? (
            <a
              href={paperData.web_url}
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
          {paperData.pdf_url ? (
            <a
              href={paperData.pdf_url}
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
        </div> */}
      </div> 
    </div>
  );
}

function SummaryBox({ title, text, color, borderColor }: any) {
  return (
    <div style={{ padding: 20, borderRadius: 18, background: color, border: `1px solid ${borderColor}` }}>
      <div style={{ fontWeight: 800, marginBottom: 8, fontSize: 16 }}>{title}</div>
      <div style={{ fontSize: 15, lineHeight: 1.7, color: "#2c2f3a" }}>
        {text || `${title} 섹션에 대한 상세 요약을 불러오는 중입니다.`}
      </div>
    </div>
  );
}