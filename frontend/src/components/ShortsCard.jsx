import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { postEvent } from "../api/events";

export default function ShortsCard({ item, userId }) {
  const nav = useNavigate();
  const cardRef = useRef(null);

  const [liked, setLiked] = useState(Boolean(item?.is_liked));
  const [bookmarked, setBookmarked] = useState(Boolean(item?.is_bookmarked));

  const [likeBusy, setLikeBusy] = useState(false);
  const [bookmarkBusy, setBookmarkBusy] = useState(false);
  const [detailBusy, setDetailBusy] = useState(false);

  // for impression
  const [impressionSent, setImpressionSent] = useState(false);

  useEffect(() => {
    setLiked(Boolean(item?.is_liked));
    setBookmarked(Boolean(item?.is_bookmarked));
    setImpressionSent(false); // 카드 바뀌면 다시 impression 가능
  }, [item?.paper_id]);

  // 화면에 실제로 보일 때 view(impression) 저장
  useEffect(() => {
    if (!userId || !item?.paper_id) return;
    if (!cardRef.current) return;
    if (impressionSent) return;

    const obs = new IntersectionObserver(
      async (entries) => {
        const entry = entries[0];
        if (!entry?.isIntersecting) return;

        try {
          await postEvent({
            userId,
            paperId: item.paper_id,
            eventType: "impression", 
          });
          setImpressionSent(true);
          obs.disconnect();
        } catch (e) {
          console.error("impression error:", e);
        }
      },
      { threshold: 0.6 } // 60% 이상 보이면 view로 간주
    );

    obs.observe(cardRef.current);
    return () => obs.disconnect();
  }, [userId, item?.paper_id, impressionSent]);

  const year = item?.published_at ? String(item.published_at).slice(0, 4) : "";

  const uniqTags = useMemo(() => {
    const tags = [];
    if (item?.primary_category) tags.push(`#${item.primary_category}`);
    if (item?.categories) {
      const extra = String(item.categories)
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      for (const t of extra.slice(0, 2)) tags.push(`#${t}`);
    }
    return Array.from(new Set(tags.filter(Boolean)));
  }, [item?.primary_category, item?.categories]);

  const onToggleLike = async () => {
    if (likeBusy) return;
    setLikeBusy(true);
    try {
      const r = await postEvent({
        userId,
        paperId: item.paper_id,
        eventType: "like",
      });
      if (typeof r.active === "boolean") setLiked(r.active);
    } catch (e) {
      console.error("like toggle error:", e);
      alert(String(e));
    } finally {
      setLikeBusy(false);
    }
  };

  const onToggleBookmark = async () => {
    if (bookmarkBusy) return;
    setBookmarkBusy(true);
    try {
      const r = await postEvent({
        userId,
        paperId: item.paper_id,
        eventType: "bookmark",
      });
      if (typeof r.active === "boolean") setBookmarked(r.active);
    } catch (e) {
      console.error("bookmark toggle error:", e);
      alert(String(e));
    } finally {
      setBookmarkBusy(false);
    }
  };

  const onDetail = async () => {
    if (detailBusy) return;
    setDetailBusy(true);
    try {
      await postEvent({
        userId,
        paperId: item.paper_id,
        eventType: "click",
      });
      nav(`/papers/${item.paper_id}`, { state: { item, userId } });
    } catch (e) {
      console.error("detail click error:", e);
      alert(String(e));
    } finally {
      setDetailBusy(false);
    }
  };

  return (
    <div className="shorts-card" ref={cardRef}>
      <div className="shorts-meta">
        <span className="shorts-year">{year}</span>
      </div>

      <div className="shorts-title">{item?.title}</div>

      <div className="shorts-abstract">
        {item?.abstract ? item.abstract : "(abstract 없음)"}
      </div>

      <div className="shorts-tags">
        {uniqTags.slice(0, 3).map((t) => (
          <span key={t} className="shorts-tag">
            {t}
          </span>
        ))}
      </div>

      <div className="shorts-actions">
        <button
          className={`shorts-btn ghost ${liked ? "on" : ""}`}
          onClick={onToggleLike}
          disabled={likeBusy}
          title={liked ? "좋아요 취소" : "좋아요"}
        >
          {likeBusy ? "..." : liked ? "👍 좋아요 취소" : "👍 좋아요"}
        </button>

        <button
          className={`shorts-btn ghost ${bookmarked ? "on" : ""}`}
          onClick={onToggleBookmark}
          disabled={bookmarkBusy}
          title={bookmarked ? "북마크 취소" : "북마크"}
        >
          {bookmarkBusy ? "..." : bookmarked ? "🔖 북마크 취소" : "🔖 북마크"}
        </button>

        <button
          className="shorts-btn primary"
          onClick={onDetail}
          disabled={detailBusy}
        >
          {detailBusy ? "..." : "자세히 보기"}
        </button>
      </div>
    </div>
  );
}
