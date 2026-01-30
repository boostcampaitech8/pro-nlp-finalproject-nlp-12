import { useLocation, useNavigate } from "react-router-dom";

export default function PaperDetailPage() {
  const nav = useNavigate();
  const { state } = useLocation();
  const item = state?.item;

  if (!item) {
    return (
      <div style={{ padding: 24 }}>
        <h2>데이터가 없습니다</h2>
        <button onClick={() => nav(-1)}>뒤로가기</button>
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: "0 auto" }}>
      <button
        onClick={() => nav(-1)}
        style={{
          padding: "10px 14px",
          borderRadius: 10,
          border: "1px solid rgba(0,0,0,0.15)",
          background: "white",
          cursor: "pointer",
        }}
      >
        ← 피드로
      </button>

      <div style={{ marginTop: 18 }}>
        <div style={{ opacity: 0.7, fontSize: 14 }}>{item.published_at?.slice(0, 4) ?? ""}</div>
        <h1 style={{ marginTop: 10, lineHeight: 1.25 }}>{item.title}</h1>

        <div style={{ marginTop: 10, opacity: 0.8 }}>
          <b>Authors</b>: {item.authors}
        </div>

        <div
          style={{
            marginTop: 18,
            padding: 16,
            borderRadius: 14,
            border: "1px solid rgba(0,0,0,0.10)",
            background: "rgba(0,0,0,0.03)",
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
          }}
        >
          {item.abstract || "(abstract 없음)"}
        </div>

        <div style={{ marginTop: 18, display: "flex", gap: 10, flexWrap: "wrap" }}>
          {item.abs_url && (
            <a
              href={item.abs_url}
              target="_blank"
              rel="noreferrer"
              style={{
                padding: "10px 14px",
                borderRadius: 10,
                border: "1px solid rgba(0,0,0,0.15)",
                textDecoration: "none",
                color: "black",
              }}
            >
              arXiv 페이지
            </a>
          )}
          {item.pdf_url && (
            <a
              href={item.pdf_url}
              target="_blank"
              rel="noreferrer"
              style={{
                padding: "10px 14px",
                borderRadius: 10,
                border: "1px solid rgba(0,0,0,0.15)",
                textDecoration: "none",
                color: "black",
              }}
            >
              PDF 보기
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
