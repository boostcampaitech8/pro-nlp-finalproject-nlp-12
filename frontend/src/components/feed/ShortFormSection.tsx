"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FeedItem, postEvent } from "../../lib/api";
import { getUserId } from "../../lib/user";
import { useLibraryState } from "../common/useLibraryState";

import { ChevronUp, ChevronDown, Pause, Play, ExternalLink } from "lucide-react";

type PendingKey = `${number}:${"like" | "bookmark"}`;

export default function ShortFormSection({
  items,
  onNeedMore,
  navBarHeight = 64,
  durationMs = 10_000,
}: {
  items: FeedItem[];
  onNeedMore?: () => void;
  navBarHeight?: number;
  durationMs?: number;
}) {
  const router = useRouter();
  const userId = getUserId()!;
  const { isActive, toggle, loading: libLoading, err: libErr } = useLibraryState(userId);

  const [idx, setIdx] = useState(0);
  const [pending, setPending] = useState<Set<PendingKey>>(new Set());
  const [toast, setToast] = useState<string | null>(null);

  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(false);

  const [progress, setProgress] = useState(0);
  const [navH, setNavH] = useState(navBarHeight);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [transitionDir, setTransitionDir] = useState<"next" | "prev">("next");

  const impressedRef = useRef<Set<number>>(new Set());

  const timerRef = useRef<number | null>(null);
  const startedAtRef = useRef<number>(0);
  const elapsedRef = useRef<number>(0);

  const cur = useMemo(() => items?.[idx], [items, idx]);

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

  useEffect(() => {
    if (idx >= (items?.length ?? 0)) setIdx(0);
  }, [idx, items?.length]);

  useEffect(() => {
    if (!cur?.paper_id) return;
    setIsTransitioning(true);
    const t = window.setTimeout(() => setIsTransitioning(false), 260);
    return () => window.clearTimeout(t);
  }, [cur?.paper_id]);

  useEffect(() => {
    const el = document.getElementById("bottom-nav");
    if (!el) {
      setNavH(navBarHeight);
      return;
    }

    const update = () => {
      const h = el.getBoundingClientRect().height;
      setNavH(h || navBarHeight);
    };

    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [navBarHeight]);

  useEffect(() => {
    if (!cur?.paper_id) return;
    if (impressedRef.current.has(cur.paper_id)) return;
    impressedRef.current.add(cur.paper_id);

    postEvent({
      user_id: userId,
      paper_id: cur.paper_id,
      event_type: "impression",
    }).catch(console.error);
  }, [cur?.paper_id, userId]);

  const goNext = useCallback(() => {
    if (!items?.length) return;
    setTransitionDir("next");
    setPaused(false);
    // 다음으로 넘어갈 때 "이번 카드에서 누적된 시간" 초기화
    elapsedRef.current = 0;
    startedAtRef.current = Date.now();
    setProgress(0);

    setIdx((v) => (v + 1) % items.length);
  }, [items?.length]);

  const goPrev = useCallback(() => {
    if (!items?.length) return;
    setTransitionDir("prev");
    setPaused(false);
    // 이전으로 넘어갈 때도 동일하게 초기화
    elapsedRef.current = 0;
    startedAtRef.current = Date.now();
    setProgress(0);

    setIdx((v) => (v - 1 + items.length) % items.length);
  }, [items?.length]);

  const togglePause = useCallback(() => {
    setPaused((p) => !p);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current != null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    stopTimer();
    startedAtRef.current = Date.now();

    timerRef.current = window.setInterval(() => {
      if (pausedRef.current) return;

      const now = Date.now();
      const elapsed = elapsedRef.current + (now - startedAtRef.current);
      const p = Math.min(1, elapsed / durationMs);

      setProgress(p);

      if (p >= 1) {
        // 다음으로 넘기기
        elapsedRef.current = 0;
        startedAtRef.current = Date.now();
        setProgress(0);
        setIdx((v) => (v + 1) % (items?.length || 1));
      }
    }, 50);
  }, [stopTimer, durationMs, items?.length]);

  useEffect(() => {
    elapsedRef.current = 0;
    startedAtRef.current = Date.now();
    setProgress(0);

    if (items?.length) startTimer();
    return () => stopTimer();
  }, [cur?.paper_id, items?.length, startTimer, stopTimer]);

  useEffect(() => {
    if (paused) {
      const now = Date.now();
      elapsedRef.current += now - startedAtRef.current; 
      // progress는 유지(리셋 X)
    } else {
      startedAtRef.current = Date.now(); 
    }
  }, [paused]);

  useEffect(() => {
    if (!onNeedMore) return;
    if (!items?.length) return;

    if (items.length - 1 - idx <= 5) onNeedMore();
  }, [idx, items?.length, onNeedMore]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const tag = (document.activeElement as HTMLElement | null)?.tagName?.toLowerCase();
      if (
        tag === "input" ||
        tag === "textarea" ||
        (document.activeElement as HTMLElement | null)?.isContentEditable
      ) {
        return;
      }

      if (e.key === "ArrowDown" || e.key === "ArrowRight") {
        e.preventDefault();
        goNext();
      } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
        e.preventDefault();
        goPrev();
      } else if (e.key === " " || e.key === "Spacebar") {
        e.preventDefault();
        togglePause();
      }
    };

    window.addEventListener("keydown", onKeyDown, { passive: false });
    return () => window.removeEventListener("keydown", onKeyDown as any);
  }, [goNext, goPrev, togglePause]);

  async function onToggle(kind: "like" | "bookmark") {
    if (!cur) return;
    const key: PendingKey = `${cur.paper_id}:${kind}`;
    if (pending.has(key)) return;

    setPending((prev) => new Set(prev).add(key));
    try {
      const active = await toggle(cur.paper_id, kind);
      setToast(active ? `${kind} ON` : `${kind} OFF`);
      window.setTimeout(() => setToast(null), 800);
    } catch (e: any) {
      setToast("네트워크 오류로 되돌렸어");
      window.setTimeout(() => setToast(null), 1200);
      console.error(e);
    } finally {
      setPending((prev) => {
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    }
  }

  const onDetail = useCallback(() => {
    if (!cur) return;
  
    console.log("onDetail cur =", cur);
    console.log("onDetail cur.paper_id =", cur.paper_id);
  
    const paperId = cur.paper_id; 
  
    if (paperId === undefined || paperId === null) {
      console.error("paper_id is missing. cur =", cur);
      return;
    }
  
    try {
      sessionStorage.setItem(`paper:${paperId}`, JSON.stringify(cur));
    } catch {}
  
    router.push(`/paper/${paperId}`);
  }, [cur, router]);

  if (!cur) return <div style={{ padding: 16 }}>표시할 논문이 없습니다.</div>;

  const liked = isActive(cur.paper_id, "like");
  const bookmarked = isActive(cur.paper_id, "bookmark");

  const likeKey: PendingKey = `${cur.paper_id}:like`;
  const bmKey: PendingKey = `${cur.paper_id}:bookmark`;
  const likeDisabled = pending.has(likeKey);
  const bmDisabled = pending.has(bmKey);

  return (
    <div
      style={{
        height: "100%",
        display: "grid",
        placeItems: "center",
        padding: "24px 16px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          pointerEvents: "none",
          zIndex: 0,
        }}
      >
        <div
          style={{
            position: "absolute",
            width: 520,
            height: 520,
            left: "-10%",
            top: "-15%",
            background: "radial-gradient(circle, rgba(255, 107, 0, 0.22), transparent 65%)",
            filter: "blur(4px)",
          }}
        />
        <div
          style={{
            position: "absolute",
            width: 620,
            height: 620,
            right: "-15%",
            bottom: "-20%",
            background: "radial-gradient(circle, rgba(0, 194, 168, 0.2), transparent 68%)",
            filter: "blur(6px)",
          }}
        />
      </div>
      {toast && (
        <div
          style={{
            position: "fixed",
            left: "50%",
            transform: "translateX(-50%)",
            bottom: navH + 40,
            background: "rgba(0,0,0,0.82)",
            color: "white",
            padding: "8px 12px",
            borderRadius: 999,
            fontSize: 12,
            zIndex: 60,
          }}
        >
          {toast}
        </div>
      )}

      <div
        style={{
          position: "fixed",
          left: 0,
          right: 0,
          bottom: navH,
          height: 6,
          background: "rgba(17, 18, 24, 0.08)",
          zIndex: 40,
          pointerEvents: "none",
          borderRadius: 0,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${Math.min(100, Math.max(0, progress * 100))}%`,
            background: "linear-gradient(90deg, #ff6b00 0%, #ff2d55 60%, #ff9a3c 100%)",
            transition: "width 0.05s linear",
            boxShadow: "0 0 12px rgba(255, 107, 0, 0.55)",
          }}
        />
      </div>

      <div
        style={{
          width: "min(980px, 100%)",
          display: "grid",
          gridTemplateColumns: "1fr 96px",
          gap: 20,
          alignItems: "center",
          position: "relative",
          zIndex: 1,
          animation: isTransitioning
            ? transitionDir === "next"
              ? "slideInUpShorts 260ms ease both"
              : "slideInDownShorts 260ms ease both"
            : undefined,
        }}
      >
        <div
          style={{
            border: "1px solid rgba(17, 18, 24, 0.08)",
            borderRadius: 22,
            overflow: "hidden",
            boxShadow: "0 18px 50px rgba(17, 18, 24, 0.18)",
            background: "rgba(255, 255, 255, 0.9)",
            color: "#111218",
            opacity: 1,
            filter: "none",
            backdropFilter: "blur(12px)",
            height: "min(70dvh, 640px)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ padding: 20, borderBottom: "1px solid rgba(17, 18, 24, 0.08)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
              <div style={{ fontWeight: 700, fontSize: 22, lineHeight: 1.2, letterSpacing: "-0.02em" }}>
                {cur.title}
              </div>
            </div>

            <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap", fontSize: 12, color: "#3a3d4a" }}>
              {cur.primary_category && (
                <span
                  style={{
                    padding: "4px 8px",
                    borderRadius: 999,
                    background: "rgba(17, 18, 24, 0.06)",
                    border: "1px solid rgba(17, 18, 24, 0.08)",
                  }}
                >
                  • {cur.primary_category}
                </span>
              )}
              {cur.published_at && (
                <span
                  style={{
                    padding: "4px 8px",
                    borderRadius: 999,
                    background: "rgba(0, 194, 168, 0.12)",
                    border: "1px solid rgba(0, 194, 168, 0.35)",
                    color: "#0b4f45",
                  }}
                >
                  • {cur.published_at.slice(0, 10)}
                </span>
              )}
            </div>

            {libLoading && <div style={{ marginTop: 8, fontSize: 12, opacity: 0.6 }}>내 라이브러리 불러오는 중…</div>}
            {libErr && <div style={{ marginTop: 8, fontSize: 12, color: "crimson" }}>{libErr}</div>}
          </div>

          <div style={{ padding: 20, flex: 1, display: "flex" }}>
            <div
              style={{
                fontSize: 14,
                lineHeight: 1.65,
                opacity: 0.9,
                display: "-webkit-box",
                WebkitLineClamp: 10,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
                background: "rgba(17, 18, 24, 0.04)",
                border: "1px solid rgba(17, 18, 24, 0.06)",
                borderRadius: 16,
                padding: 14,
                width: "100%",
              }}
            >
              {cur.abstract}
            </div>
          </div>

          <div
            style={{
              padding: 18,
              borderTop: "1px solid rgba(17, 18, 24, 0.08)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 10,
              flexWrap: "wrap",
            }}
          >
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <button
                onClick={() => onToggle("like")}
                disabled={likeDisabled}
                aria-pressed={liked}
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  border: "1px solid rgba(255, 107, 0, 0.4)",
                  opacity: likeDisabled ? 0.6 : 1,
                  fontWeight: 800,
                  cursor: likeDisabled ? "not-allowed" : "pointer",
                  background: liked ? "rgba(255, 107, 0, 0.16)" : "white",
                  boxShadow: liked ? "0 6px 16px rgba(255, 107, 0, 0.2)" : "none",
                }}
              >
                {liked ? "❤️ Liked" : "🤍 Like"}
              </button>

              <button
                onClick={() => onToggle("bookmark")}
                disabled={bmDisabled}
                aria-pressed={bookmarked}
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  border: "1px solid rgba(17, 18, 24, 0.16)",
                  opacity: bmDisabled ? 0.6 : 1,
                  fontWeight: 800,
                  cursor: bmDisabled ? "not-allowed" : "pointer",
                  background: bookmarked ? "rgba(17, 18, 24, 0.08)" : "white",
                }}
              >
                {bookmarked ? "🔖 Bookmarked" : "📑 Bookmark"}
              </button>

              <button
                onClick={onDetail}
                style={{
                  padding: "10px 14px",
                  borderRadius: 999,
                  border: "1px solid rgba(17, 18, 24, 0.1)",
                  fontWeight: 900,
                  cursor: "pointer",
                  background: "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)",
                  color: "white",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 6
                }}
              ><ExternalLink size={14} style={{ verticalAlign: "middle", marginLeft: 6 }} />
                자세히 보기 
              </button>
            </div>

            <div
              style={{
                opacity: 0.7,
                fontSize: 12,
                padding: "6px 10px",
                borderRadius: 999,
                background: "rgba(17, 18, 24, 0.06)",
                border: "1px solid rgba(17, 18, 24, 0.08)",
              }}
            >
              키보드: ↑ 이전 / ↓ 다음 / Space 일시정지
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "stretch" }}>
          <button
            onClick={goPrev}
            style={{
              height: 46,
              borderRadius: 16,
              border: "1px solid rgba(17, 18, 24, 0.12)",
              background: "rgba(255,255,255,0.92)",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
              boxShadow: "0 10px 20px rgba(17, 18, 24, 0.12)",
              color: "#8d90a1"
            }}
            title="이전 (↑)"
          >
            <ChevronUp />
          </button>

          <button
            onClick={goNext}
            style={{
              height: 46,
              borderRadius: 16,
              border: "1px solid rgba(17, 18, 24, 0.12)",
              background: "rgba(255,255,255,0.92)",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
              boxShadow: "0 10px 20px rgba(17, 18, 24, 0.12)",
              color: "#8d90a1"
            }}
            title="다음 (↓)"
          >
            <ChevronDown />
          </button>

          <button
            onClick={togglePause}
            style={{
              height: 46,
              borderRadius: 16,
              border: "1px solid rgba(17, 18, 24, 0.12)",
              background: paused
                ? "linear-gradient(135deg, #ff6b00 0%, #ff2d55 100%)"
                : "rgba(255,255,255,0.92)",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
              boxShadow: "0 10px 20px rgba(17, 18, 24, 0.12)",
            }}
            title="일시정지/재생 (Space)"
          >
            {paused ? <Play color="white" /> : <Pause color="#8d90a1" />}
          </button>
        </div>
      </div>
    </div>
  );
}
