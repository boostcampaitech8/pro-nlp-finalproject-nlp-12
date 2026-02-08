"use client";

import Link from "next/link";
import { User } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

export default function AppHeader() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const paramQ = searchParams?.get("q") ?? "";
  const [q, setQ] = useState(paramQ);

  useEffect(() => {
    setQ(paramQ);
  }, [paramQ]);

  const showSearch = !pathname?.startsWith("/onboarding");

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    const term = q.trim();
    if (!term) {
      router.push("/search");
      return;
    }
    router.push(`/search?q=${encodeURIComponent(term)}`);
  }

  return (
    <header style={{ position: "sticky", top: 0, zIndex: 50, width: "100%" }}>
      <div
        style={{
          height: 72,
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
            whiteSpace: "nowrap",
          }}
        >
          <span
            style={{
              padding: "9px 14px",
              borderRadius: 10,
              background: "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)",
              color: "white",
              fontWeight: 800,
              fontSize: 14,
              letterSpacing: "0.06em",
            }}
          >
            10 seconds
          </span>
        </Link>

        {showSearch && (
          <form
            onSubmit={onSubmit}
            style={{
              flex: "0 1 520px",
              display: "flex",
              alignItems: "center",
              gap: 10,
              maxWidth: 520,
              margin: "0 12px",
            }}
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Search papers, topics, keywords"
              style={{
                flex: 1,
                padding: "6px 12px",
                border: "1px solid rgba(17, 18, 24, 0.12)",
                borderRadius: 14,
                background: "white",
                fontSize: 14,
                color: "#111218",
              }}
            />
            <button
              type="submit"
              style={{
                padding: "5px 12px",
                borderRadius: 14,
                border: "1px solid rgba(255, 107, 0, 0.4)",
                background: "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)",
                color: "white",
                fontWeight: 700,
                fontSize: 13,
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              Search
            </button>
          </form>
        )}

        <Link
          href="/mypage"
          aria-label="My Page"
          style={{
            width: 36,
            height: 36,
            borderRadius: 999,
            border: "1px solid rgba(17, 18, 24, 0.12)",
            color: "#111218",
            textDecoration: "none",
            display: "grid",
            placeItems: "center",
            background: "rgba(255, 255, 255, 0.9)",
          }}
        >
          <User size={18} />
        </Link>
      </div>
    </header>
  );
}
