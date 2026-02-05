"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { href: "/home", label: "recommend" },
  { href: "/search", label: "search" },
  { href: "/timeline", label: "timeline" },
  { href: "/mypage", label: "mypage" },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav
      id="bottom-nav"
      style={{
        position: "sticky",
        bottom: 0,
        margin: 0,
        padding: "6px 8px",
        borderRadius: 0,
        background: "rgba(255,255,255,0.9)",
        borderTop: "1px solid rgba(17,18,24,0.08)",
        boxShadow: "0 -8px 18px rgba(17, 18, 24, 0.08)",
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: 6,
        backdropFilter: "blur(10px)",
      }}
    >
      {items.map((it) => {
        const active = pathname === it.href;
        return (
          <Link
            key={it.href}
            href={it.href}
            style={{
              padding: "10px 8px",
              textAlign: "center",
              fontWeight: active ? 700 : 600,
              opacity: active ? 1 : 0.65,
              textTransform: "capitalize",
              color: active ? "#111218" : "#3a3d4a",
              borderRadius: 0,
              background: "transparent",
              borderBottom: active ? "2px solid #ff6b00" : "2px solid transparent",
              transition: "all 0.2s ease",
            }}
          >
            {it.label}
          </Link>
        );
      })}
    </nav>
  );
}
