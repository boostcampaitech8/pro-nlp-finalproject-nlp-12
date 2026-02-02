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
      style={{
        position: "sticky",
        bottom: 0,
        borderTop: "1px solid red",
        background: "white",
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
      }}
    >
      {items.map((it) => {
        const active = pathname === it.href;
        return (
          <Link
            key={it.href}
            href={it.href}
            style={{
              padding: 12,
              textAlign: "center",
              fontWeight: active ? 700 : 500,
              opacity: active ? 1 : 0.6,
              textTransform: "capitalize",
            }}
          >
            {it.label}
          </Link>
        );
      })}
    </nav>
  );
}
