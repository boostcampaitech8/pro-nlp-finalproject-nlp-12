"use client";

import { useEffect, useMemo, useState } from "react";
import { getLibrary, postEvent } from "../../lib/api";

type Kind = "like" | "bookmark";

export function useLibraryState(userId: string) {
  const [liked, setLiked] = useState<Set<number>>(new Set());
  const [bookmarked, setBookmarked] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  // 초기 상태: 내 라이브러리(좋아요/북마크) 한번에 로딩
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        setErr(null);
        const out = await getLibrary(userId, "all");
        if (!alive) return;

        const likeSet = new Set<number>();
        const bmSet = new Set<number>();

        for (const it of out.items ?? []) {
          if (it.event_type === "like") likeSet.add(it.paper_id);
          if (it.event_type === "bookmark") bmSet.add(it.paper_id);
        }
        setLiked(likeSet);
        setBookmarked(bmSet);
      } catch (e: any) {
        if (!alive) return;
        setErr(String(e?.message ?? e));
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [userId]);

  const isActive = useMemo(() => {
    return (paperId: number, kind: Kind) =>
      kind === "like" ? liked.has(paperId) : bookmarked.has(paperId);
  }, [liked, bookmarked]);

  async function toggle(paperId: number, kind: Kind) {
    const targetSet = kind === "like" ? liked : bookmarked;
    const setTarget = kind === "like" ? setLiked : setBookmarked;

    const wasActive = targetSet.has(paperId);

    setTarget((prev) => {
      const next = new Set(prev);
      if (wasActive) next.delete(paperId);
      else next.add(paperId);
      return next;
    });

    try {
      const out = await postEvent({
        user_id: userId,
        paper_id: paperId,
        event_type: kind,
      });

      setTarget((prev) => {
        const next = new Set(prev);
        if (out.active) next.add(paperId);
        else next.delete(paperId);
        return next;
      });

      return out.active;
    } catch (e) {
      setTarget((prev) => {
        const next = new Set(prev);
        if (wasActive) next.add(paperId);
        else next.delete(paperId);
        return next;
      });
      throw e;
    }
  }

  return { liked, bookmarked, isActive, toggle, loading, err };
}
