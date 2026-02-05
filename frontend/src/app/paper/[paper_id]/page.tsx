// src/app/paper/[paper_id]/page.tsx
import Link from "next/link";

type PaperDetail = {
  paper_id: number;
  title: string;
  abstract?: string | null;
  web_url?: string | null;
  pdf_url?: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

async function getPaper(paperId: string): Promise<PaperDetail> {
  const url = `${API_BASE}/api/paper/${paperId}`;
  const res = await fetch(url, { cache: "no-store" });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Failed to fetch: ${url} | HTTP ${res.status} - ${text}`);
  }
  return res.json();
}

export default async function PaperDetailPage(props: {
  params: Promise<{ paper_id: string }>;
  searchParams?: Promise<{ from?: string }>;
}) {
  const { paper_id } = await props.params;
  const searchParams = props.searchParams ? await props.searchParams : undefined;
  const backHref = searchParams?.from === "mypage" ? "/mypage" : "/home";

  const data = await getPaper(paper_id);
  const abstractText = (data.abstract || "").trim();
  const chunks = abstractText
    ? abstractText.split(/(?<=[.!?])\s+/).filter(Boolean)
    : [];
  const pick = (start: number, count: number) => chunks.slice(start, start + count).join(" ");
  const motivationText = pick(0, 2) || "동기 요약을 준비 중입니다.";
  const methodologyText = pick(2, 2) || "방법 요약을 준비 중입니다.";
  const performanceText = pick(4, 2) || "성능 요약을 준비 중입니다.";
  const significanceText = pick(6, 2) || "의의 요약을 준비 중입니다.";

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", padding: "24px 16px 120px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <Link href={backHref}>
          <button
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              border: "1px solid rgba(17, 18, 24, 0.12)",
              background: "rgba(255,255,255,0.9)",
              cursor: "pointer",
              fontWeight: 800,
              color: "#111218",
              boxShadow: "0 8px 18px rgba(17, 18, 24, 0.08)",
            }}
          >
            ← 뒤로
          </button>
        </Link>
      </div>

      <div
        style={{
          marginTop: 16,
          borderRadius: 22,
          padding: 22,
          background: "rgba(255,255,255,0.92)",
          border: "1px solid rgba(17, 18, 24, 0.08)",
          boxShadow: "0 18px 50px rgba(17, 18, 24, 0.16)",
          backdropFilter: "blur(12px)",
          color: "#111218",
        }}
      >
        <h1 style={{ fontSize: 24, fontWeight: 800, lineHeight: 1.25, letterSpacing: "-0.02em" }}>
          {data.title}
        </h1>

        <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
          <div
            style={{
              padding: 16,
              borderRadius: 16,
              background: "rgba(255, 107, 0, 0.08)",
              border: "1px solid rgba(255, 107, 0, 0.2)",
            }}
          >
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Motivation</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: "#2c2f3a" }}>{motivationText}</div>
          </div>
          <div
            style={{
              padding: 16,
              borderRadius: 16,
              background: "rgba(0, 194, 168, 0.08)",
              border: "1px solid rgba(0, 194, 168, 0.2)",
            }}
          >
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Methodology</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: "#2c2f3a" }}>{methodologyText}</div>
          </div>
          <div
            style={{
              padding: 16,
              borderRadius: 16,
              background: "rgba(17, 18, 24, 0.04)",
              border: "1px solid rgba(17, 18, 24, 0.08)",
            }}
          >
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Performance</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: "#2c2f3a" }}>{performanceText}</div>
          </div>
          <div
            style={{
              padding: 16,
              borderRadius: 16,
              background: "rgba(255, 45, 85, 0.08)",
              border: "1px solid rgba(255, 45, 85, 0.2)",
            }}
          >
            <div style={{ fontWeight: 800, marginBottom: 6 }}>Significance</div>
            <div style={{ fontSize: 14, lineHeight: 1.7, color: "#2c2f3a" }}>{significanceText}</div>
          </div>
        </div>

        <div style={{ marginTop: 18, display: "flex", gap: 10, flexWrap: "wrap" }}>
          {data.web_url ? (
            <a
              href={data.web_url}
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
          {data.pdf_url ? (
            <a
              href={data.pdf_url}
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
