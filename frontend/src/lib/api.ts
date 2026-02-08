// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "https://10seconds.yeni-lab.org/api";

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
  arxiv_id?: string | null;
  title: string;
  published_date?: string | null;
  pdf_url?: string | null;
  abs_url?: string | null;
  summary?: string;
  primary_category?: string | null;
  categories?: any | null;
  is_liked: boolean;
  is_bookmarked: boolean;
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
export async function searchFeed(user_id: string, query: string) {
  return http<FeedItem[]>(`/search/`, {
    method: "POST",
    body: JSON.stringify({ user_id, query }),
  });
}

export async function postEvent(input: {
  user_id: string;
  paper_id: number;
  event_type:  "click" | "like" | "bookmark" | "impression";
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

/*
* 논문 요약 관련 스키마
*/
export type SummaryDetail = {
  summary_type: string;
  summary_text: string;
}

export type SummaryItem = {
  paper_id: number;
  pdf_url: string;
  abs_url: string;
  summaries: SummaryDetail[];
}

/*
* 클릭 이벤트 저장 및 논문 요약본 배열 반환
*/
export async function getPaperSummary(user_id: string, paper_id: number | null = null, arxiv_id: string | null = null) {
  return http<SummaryItem>(`/summary/`, {
    method: "POST",
    body: JSON.stringify({ user_id, paper_id, arxiv_id })
  });
}

export async function postOnboarding(input: { user_id: string; categories: string[] }) {
  return http<{ user_id: string; has_onboarded: boolean }>(`/users/onboarding`, {
    method: "POST",
    body: JSON.stringify({
      user_id: input.user_id,
      answers: { categories: input.categories },
    }),
  });
}
