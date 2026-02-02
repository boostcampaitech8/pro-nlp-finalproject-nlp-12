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
}) {
  // ✅ Next 16 Turbopack: params가 Promise일 수 있음
  const { paper_id } = await props.params;

  const data = await getPaper(paper_id);

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: 20 }}>
      <Link href="/home">
        <button
          style={{
            padding: "8px 12px",
            borderRadius: 10,
            border: "1px solid #ddd",
            background: "white",
            cursor: "pointer",
            fontWeight: 800,
            color: "black"
          }}
        >
          ← 뒤로
        </button>
      </Link>

      <h1 style={{ marginTop: 16, fontSize: 22, fontWeight: 900 }}>
        {data.title}
      </h1>

      <p style={{ marginTop: 14, lineHeight: 1.65, whiteSpace: "pre-wrap" }}>
        {data.abstract || "(abstract 없음)"}
      </p>

      <div style={{ marginTop: 18, display: "flex", gap: 10, flexWrap: "wrap" }}>
        {data.web_url ? (
          <a href={data.web_url} target="_blank" rel="noreferrer">
            Web 링크
          </a>
        ) : null}
        {data.pdf_url ? (
          <a href={data.pdf_url} target="_blank" rel="noreferrer">
            PDF 링크
          </a>
        ) : null}
      </div>
    </div>
  );
}
