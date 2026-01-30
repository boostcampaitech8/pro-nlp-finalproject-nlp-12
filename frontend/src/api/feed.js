// src/api/feed.js
export async function getFeed({ userId, limit, cursor }) {
  if (!userId || String(userId).trim().length === 0) {
    throw new Error("feed failed: missing userId");
  }

  const qs = new URLSearchParams();
  qs.set("user_id", String(userId));
  qs.set("k", String(limit ?? 20));
  if (cursor) qs.set("cursor", String(cursor));

  const url = `/api/feed?${qs.toString()}`;
  const res = await fetch(url);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`feed failed: ${res.status} ${text}`);
  }
  return res.json();
}
