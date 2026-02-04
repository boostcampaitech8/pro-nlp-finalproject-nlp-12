"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getLibrary } from "../../lib/api";
import { getUserId } from "../../lib/user";

export default function MyPage() {
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [view, setView] = useState<"like" | "bookmark">("like");

  useEffect(() => {
    const uid = getUserId()!;
    (async () => {
      try {
        const out = await getLibrary(uid, "all");
        setItems(out.items ?? []);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      }
    })();
  }, []);

  const likeItems = items.filter((it) => it.event_type === "like");
  const bookmarkItems = items.filter((it) => it.event_type === "bookmark");
  const filteredItems = view === "like" ? likeItems : bookmarkItems;

  if (err) return <div style={{ padding: 16 }}>에러: {err}</div>;

  return (
    <div style={{ padding: 20, display: "grid", placeItems: "center" }}>
      <div
        style={{
          width: "min(980px, 100%)",
          borderRadius: 22,
          padding: 20,
          background: "rgba(255,255,255,0.92)",
          border: "1px solid rgba(17, 18, 24, 0.08)",
          boxShadow: "0 18px 50px rgba(17, 18, 24, 0.16)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", color: "#111218" }}>
              My Library
            </div>
            <div style={{ marginTop: 4, fontSize: 13, color: "#2c2f3a" }}>좋아요와 북마크를 분리해서 확인하세요.</div>
          </div>
          <div
            style={{
              padding: "6px 10px",
              borderRadius: 999,
              background: "rgba(255, 107, 0, 0.12)",
              border: "1px solid rgba(255, 107, 0, 0.35)",
              color: "#7a3100",
              fontSize: 12,
              fontWeight: 700,
            }}
          >
            {items.length} items
          </div>
        </div>

        <div style={{ marginTop: 14, display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            onClick={() => setView("like")}
            style={{
              padding: "8px 12px",
              borderRadius: 999,
              border: view === "like" ? "1px solid rgba(255, 107, 0, 0.45)" : "1px solid rgba(17, 18, 24, 0.12)",
              background: view === "like" ? "rgba(255, 107, 0, 0.12)" : "white",
              color: "#111218",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            좋아요 ({likeItems.length})
          </button>
          <button
            onClick={() => setView("bookmark")}
            style={{
              padding: "8px 12px",
              borderRadius: 999,
              border: view === "bookmark" ? "1px solid rgba(0, 194, 168, 0.45)" : "1px solid rgba(17, 18, 24, 0.12)",
              background: view === "bookmark" ? "rgba(0, 194, 168, 0.12)" : "white",
              color: "#111218",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            북마크 ({bookmarkItems.length})
          </button>
        </div>

        {filteredItems.length == 0 ? (
          <div style={{ marginTop: 16, color: "#2c2f3a", opacity: 0.75 }}>선택한 항목이 없습니다.</div>
        ) : (
          <ul style={{ display: "grid", gap: 12, marginTop: 16 }}>
            {filteredItems.map((it) => (
              <li
                key={`${it.paper_id}-${it.event_type}`}
                style={{
                  border: "1px solid rgba(17, 18, 24, 0.08)",
                  padding: 14,
                  borderRadius: 16,
                  background: "white",
                  boxShadow: "0 8px 18px rgba(17, 18, 24, 0.08)",
                }}
              >
                <div style={{ fontWeight: 800, color: "#111218" }}>
                  <Link href={`/paper/${it.paper_id}?from=mypage`}>{it.title}</Link>
                </div>
                <div style={{ opacity: 0.78, marginTop: 6, fontSize: 13, color: "#2c2f3a" }}>{it.abstract}</div>
                <div style={{ marginTop: 10 }}>
                  <Link
                    href={`/paper/${it.paper_id}?from=mypage`}
                    style={{
                      display: "inline-flex",
                      padding: "8px 12px",
                      borderRadius: 12,
                      border: "1px solid rgba(17, 18, 24, 0.12)",
                      background: "white",
                      fontWeight: 700,
                      color: "#111218",
                    }}
                  >
                    자세히 보기
                  </Link>
                </div>
                <div
                  style={{
                    marginTop: 10,
                    fontSize: 11,
                    display: "inline-flex",
                    padding: "4px 8px",
                    borderRadius: 999,
                    background:
                      it.event_type === "bookmark"
                        ? "rgba(0, 194, 168, 0.12)"
                        : "rgba(255, 107, 0, 0.12)",
                    border:
                      it.event_type === "bookmark"
                        ? "1px solid rgba(0, 194, 168, 0.35)"
                        : "1px solid rgba(255, 107, 0, 0.35)",
                    color: it.event_type === "bookmark" ? "#0b4f45" : "#7a3100",
                    fontWeight: 700,
                  }}
                >
                  {it.event_type === "bookmark" ? "북마크" : "좋아요"}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
