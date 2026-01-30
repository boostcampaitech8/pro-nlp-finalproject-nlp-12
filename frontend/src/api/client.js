export async function apiGet(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  const url = p.startsWith("/api/") ? p : `/api${p}`;

  const res = await fetch(url);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GET ${url} -> ${res.status}\n${text}`);
  }

  return res.json();
}
