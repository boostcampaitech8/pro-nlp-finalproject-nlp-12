"use client";

import Link from "next/link";

export default function AppHeader() {
  return (
    <header style={{ position: "sticky", top: 0, zIndex: 50, width: "100%" }}>
      <div
        style={{
          height: 56,
          padding: "0 16px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 12,
          background: "rgba(255, 255, 255, 0.85)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid rgba(17, 18, 24, 0.08)",
          boxShadow: "0 12px 24px rgba(17, 18, 24, 0.08)",
        }}
      >
        <Link
          href="/"
          style={{
            fontWeight: 700,
            letterSpacing: "-0.02em",
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <span
            style={{
              padding: "6px 10px",
              borderRadius: 10,
              background: "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)",
              color: "white",
              fontWeight: 800,
              fontSize: 12,
              letterSpacing: "0.06em",
            }}
          >
            10 seconds
          </span>
        </Link>
      </div>
    </header>
  );
}
