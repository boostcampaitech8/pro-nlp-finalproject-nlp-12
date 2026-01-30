import { useEffect, useRef, useState } from "react";
import ShortsCard from "./ShortsCard";
import "../styles/shorts.css";

export default function ShortsViewer({
  items,
  userId,
  loading,
  err,
  hasMore = false,
  onLoadMore, // optional
}) {
  const viewRef = useRef(null);
  const [pageH, setPageH] = useState(window.innerHeight);
  const [idx, setIdx] = useState(0);

  const wheelLockRef = useRef(false);
  const clamp = (n, len) => Math.max(0, Math.min(n, Math.max(0, len - 1)));

  useEffect(() => {
    const calc = () => {
      const h = viewRef.current?.clientHeight ?? window.innerHeight;
      setPageH(h);
    };
    calc();
    window.addEventListener("resize", calc);
    return () => window.removeEventListener("resize", calc);
  }, []);

  // items가 바뀌면 첫 장으로
  useEffect(() => {
    setIdx(0);
  }, [items?.length]);

  // 끝에 가까우면 더 불러오기
  useEffect(() => {
    if (!hasMore) return;
    if (!onLoadMore) return;
    const remaining = (items?.length ?? 0) - 1 - idx;
    if (remaining <= 2) onLoadMore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, items?.length, hasMore]);

  const goNext = () => setIdx((prev) => clamp(prev + 1, items.length));
  const goPrev = () => setIdx((prev) => clamp(prev - 1, items.length));

  const onWheel = (e) => {
    if (wheelLockRef.current) return;
    wheelLockRef.current = true;

    if (e.deltaY > 0) goNext();
    else goPrev();

    setTimeout(() => {
      wheelLockRef.current = false;
    }, 220);
  };

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowDown") goNext();
      if (e.key === "ArrowUp") goPrev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items?.length]);

  return (
    <div className="shorts-root" onWheel={onWheel}>
      {err && <div className="shorts-error">{err}</div>}

      <div className="shorts-view" ref={viewRef}>
        {items?.length > 0 ? (
          <div
            className="shorts-slide"
            style={{ transform: `translateY(${-idx * pageH}px)` }}
          >
            {items.map((item) => (
              <div key={item.paper_id} className="shorts-page">
                <ShortsCard item={item} userId={userId} />
              </div>
            ))}
          </div>
        ) : (
          <div className="shorts-empty">
            {loading ? "Loading..." : "No items"}
          </div>
        )}
      </div>

      <div className="shorts-nav">
        <button className="shorts-nav-btn" onClick={goPrev} disabled={idx === 0}>
          ▲
        </button>
        <button
          className="shorts-nav-btn"
          onClick={goNext}
          disabled={items?.length === 0 || (idx === items.length - 1 && !hasMore)}
          title={idx === items.length - 1 && !hasMore ? "No more items" : ""}
        >
          ▼
        </button>
      </div>
    </div>
  );
}
