"use client";

import { useEffect, useState } from "react";
import { getLibrary } from "../../lib/api";
import { getUserId } from "../../lib/user";

export default function MyPage() {
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

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

  if (err) return <div style={{ padding: 16 }}>에러: {err}</div>;

  return (
    <div style={{ padding: 16 }}>
      <h2 style={{ marginBottom: 12 }}>My Library</h2>
      {items.length === 0 ? (
        <div style={{ opacity: 0.7 }}>좋아요/북마크한 논문이 없습니다.</div>
      ) : (
        <ul style={{ display: "grid", gap: 10 }}>
          {items.map((it) => (
            <li key={`${it.paper_id}-${it.event_type}`} style={{ border: "1px solid #eee", padding: 12, borderRadius: 12 }}>
              <div style={{ fontWeight: 800 }}>{it.title}</div>
              <div style={{ opacity: 0.75, marginTop: 6 }}>{it.abstract}</div>
              <div style={{ marginTop: 8, fontSize: 12, opacity: 0.6 }}>{it.event_type}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
