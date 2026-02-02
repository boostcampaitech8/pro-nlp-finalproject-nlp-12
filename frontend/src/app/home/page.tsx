"use client";

import { useCallback, useEffect, useState } from "react";
import { getFeed, FeedItem } from "../../lib/api";
import { getUserId } from "../../lib/user";
import ShortFormSection from "../../components/feed/ShortFormSection";

export default function HomePage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const fetchPage = useCallback(async (cursor: string | null) => {
    const uid = getUserId();
    if (!uid) return;

    const out = await getFeed(uid, 20, cursor);

    setItems((prev) => (cursor ? [...prev, ...(out.items ?? [])] : out.items ?? []));
    setNextCursor(out.next_cursor ?? null);
    setHasMore(Boolean(out.has_more));
  }, []);

  // 최초 1페이지
  useEffect(() => {
    (async () => {
      try {
        await fetchPage(null);
      } catch (e: any) {
        setErr(String(e?.message ?? e));
      }
    })();
  }, [fetchPage]);

  // 다음 페이지(append)
  const fetchMore = useCallback(async () => {
    if (!hasMore || loadingMore || !nextCursor) return;

    setLoadingMore(true);
    try {
      await fetchPage(nextCursor);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, nextCursor, fetchPage]);

  if (err) return <div style={{ padding: 16 }}>에러: {err}</div>;

  return (
    <>
      <ShortFormSection items={items} onNeedMore={fetchMore} />
      {loadingMore && <div style={{ padding: 12, opacity: 0.6 }}>다음 추천 불러오는 중...</div>}
    </>
  );
}
