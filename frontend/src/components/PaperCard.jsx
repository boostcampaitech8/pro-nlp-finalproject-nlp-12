export default function PaperCard({ item }) {
  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 16, marginBottom: 12 }}>
      <div style={{ display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>{item.title}</h3>
        <span style={{ color: "#666" }}>({item.arxiv_id})</span>
      </div>

      <div style={{ marginTop: 8, color: "#444" }}>
        <b>Authors:</b> {item.authors}
      </div>

      <div style={{ marginTop: 6, color: "#444" }}>
        <b>Category:</b> {item.categories}
        {item.primary_category ? ` / primary: ${item.primary_category}` : ""}
      </div>

      <div style={{ marginTop: 6, color: "#444" }}>
        <b>Published:</b> {item.published_at}
      </div>

      <div style={{ marginTop: 10, whiteSpace: "pre-wrap", lineHeight: 1.4 }}>
        {item.abstract}
      </div>

      <div style={{ marginTop: 12, display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <a href={item.abs_url} target="_blank" rel="noreferrer">arXiv</a>
        <a href={item.pdf_url} target="_blank" rel="noreferrer">PDF</a>
        <span style={{ marginLeft: "auto", color: "#666" }}>
          score: {typeof item.score === "number" ? item.score.toFixed(4) : item.score}
        </span>
      </div>
    </div>
  );
}
