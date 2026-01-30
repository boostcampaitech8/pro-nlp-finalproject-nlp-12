export async function searchPapers({ userId, q, k = 20 }) {
  if (!userId) throw new Error("search failed: missing userId");
  if (!q || q.trim().length === 0) {
    throw new Error("search failed: empty query");
  }

  const qs = new URLSearchParams();
  qs.set("user_id", String(userId));
  qs.set("q", q);
  qs.set("k", String(k));

  const res = await fetch(`/api/search?${qs.toString()}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`search failed: ${res.status} ${text}`);
  }
  return res.json();
}
