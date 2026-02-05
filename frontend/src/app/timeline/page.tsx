export default function TimelinePage() {
  return (
    <div style={{ padding: 24, display: "grid", placeItems: "center", minHeight: "70dvh" }}>
      <div
        style={{
          width: "min(720px, 100%)",
          padding: 24,
          borderRadius: 22,
          background: "rgba(255,255,255,0.9)",
          border: "1px solid rgba(17, 18, 24, 0.08)",
          boxShadow: "0 18px 50px rgba(17, 18, 24, 0.16)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", color: "#111218" }}>Timeline</div>
        <div
          style={{
            marginTop: 16,
            height: 140,
            borderRadius: 16,
            background:
              "linear-gradient(135deg, rgba(255,107,0,0.15) 0%, rgba(255,45,85,0.18) 45%, rgba(0,194,168,0.18) 100%)",
            border: "1px dashed rgba(17, 18, 24, 0.18)",
            display: "grid",
            placeItems: "center",
            color: "#2c2f3a",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          Timeline graph placeholder
        </div>
      </div>
    </div>
  );
}
