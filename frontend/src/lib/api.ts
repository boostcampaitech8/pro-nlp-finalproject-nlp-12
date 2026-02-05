// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000/api";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${path} ${txt}`);
  }
  return (await res.json()) as T;
}

export type FeedItem = {
  paper_id: number;
  title: string;
  abstract: string;
  score?: number;
  arxiv_id?: string | null;
  authors?: any;
  primary_category?: string | null;
  categories?: any;
  published_at?: string | null;
  abs_url?: string | null;
  pdf_url?: string | null;

  is_liked?: boolean;
  is_bookmarked?: boolean;
};

export async function getFeed(user_id: string, k = 20, cursor?: string | null, mode?: "fast" | "quick" | "smart") {
  const c = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
  const m = mode ? `&mode=${encodeURIComponent(mode)}` : "";
  return http<{
    user_id: string;
    k?: number | null;
    limit: number;
    items: FeedItem[];
    next_cursor?: string | null;
    has_more?: boolean;
  }>(`/feed?user_id=${encodeURIComponent(user_id)}&k=${k}${c}${m}`);
}

/**
 * TODO : search 피드
 */
export async function searchFeed(user_id: string, q: string, k = 20, cursor?: string | null) {
  const c = cursor ? `&cursor=${encodeURIComponent(cursor)}` : "";
  return http<{
    user_id: string;
    q: string;
    k?: number | null;
    limit: number;
    items: FeedItem[];
    next_cursor?: string | null;
    has_more?: boolean;
  }>(`/search?user_id=${encodeURIComponent(user_id)}&q=${encodeURIComponent(q)}&k=${k}${c}`);
}

export async function postEvent(input: {
  user_id: string;
  paper_id: number;
  event_type: "impression" | "click" | "like" | "bookmark" | "dislike";
}) {
  return http<{ ok: boolean; active: boolean }>(`/events`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function getLibrary(user_id: string, type: "all" | "like" | "bookmark" = "all") {
  return http<{
    total: number;
    items: Array<{
      paper_id: number;
      event_type: "like" | "bookmark";
      title: string;
      abstract: string;
    }>;
  }>(`/me/library?user_id=${encodeURIComponent(user_id)}&type=${type}&limit=100&offset=0`);
}
