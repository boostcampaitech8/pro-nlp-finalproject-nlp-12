export async function fetchMyLibrary({ baseUrl, userId, type = "all", limit = 50, offset = 0 }) {
  const qs = new URLSearchParams({
    user_id: userId,
    type,
    limit: String(limit),
    offset: String(offset),
  });

  const res = await fetch(`${baseUrl}/me/library?${qs.toString()}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return await res.json();
}
