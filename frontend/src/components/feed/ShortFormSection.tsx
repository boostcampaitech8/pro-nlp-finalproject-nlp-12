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
    // 다음으로 넘어갈 때 "이번 카드에서 누적된 시간" 초기화
    elapsedRef.current = 0;
    startedAtRef.current = Date.now();
    setProgress(0);

    setIdx((v) => (v + 1) % items.length);
  }, [items?.length]);

  const goPrev = useCallback(() => {
    if (!items?.length) return;
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
      // ✅ 클로저 stale 방지: ref로 pause 상태 확인
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

  // ✅ 카드가 바뀌면 (진짜로 paper_id 바뀔 때만) 타이머 초기화
  useEffect(() => {
    elapsedRef.current = 0;
    startedAtRef.current = Date.now();
    setProgress(0);

    if (items?.length) startTimer();
    return () => stopTimer();
  }, [cur?.paper_id, items?.length, startTimer, stopTimer]);

  // ✅ pause 시점까지 진행된 시간 누적 / resume 시 기준점만 갱신
  useEffect(() => {
    if (paused) {
      const now = Date.now();
      elapsedRef.current += now - startedAtRef.current; // ✅ 여기서 "지금까지" 누적
      // progress는 유지(리셋 X)
    } else {
      startedAtRef.current = Date.now(); // ✅ 이어서 진행
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
    try {
      sessionStorage.setItem(`paper:${cur.paper_id}`, JSON.stringify(cur));
    } catch {}
    router.push(`/paper/${cur.paper_id}`);
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
        minHeight: "calc(100dvh - 72px)",
        display: "grid",
        placeItems: "center",
        padding: 16,
      }}
    >
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
          height: 4,
          background: "rgba(255,255,255,0.22)",
          zIndex: 9999,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${Math.min(100, Math.max(0, progress * 100))}%`,
            background: "red",
            transition: "width 0.05s linear",
          }}
        />
      </div>

      <div
        style={{
          width: "min(980px, 100%)",
          display: "grid",
          gridTemplateColumns: "1fr 92px",
          gap: 16,
          alignItems: "center",
        }}
      >
        <div
          style={{
            border: "1px solid #e5e5e5",
            borderRadius: 18,
            overflow: "hidden",
            boxShadow: "0 10px 30px rgba(0,0,0,0.15)",
            background: "#ffffff",
            color: "#111",
            opacity: 1,
            filter: "none"
          }}
        >
          <div style={{ padding: 18, borderBottom: "1px solid #f0f0f0" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <div style={{ fontWeight: 900, fontSize: 18, lineHeight: 1.25 }}>{cur.title}</div>

              
            </div>

            <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap", opacity: 0.75, fontSize: 12 }}>
              {cur.primary_category && <span>• {cur.primary_category}</span>}
              {cur.published_at && <span>• {cur.published_at.slice(0, 10)}</span>}
            </div>

            {libLoading && <div style={{ marginTop: 8, fontSize: 12, opacity: 0.6 }}>내 라이브러리 불러오는 중…</div>}
            {libErr && <div style={{ marginTop: 8, fontSize: 12, color: "crimson" }}>{libErr}</div>}
          </div>

          <div style={{ padding: 18 }}>
            <div
              style={{
                fontSize: 14,
                lineHeight: 1.65,
                opacity: 0.9,
                display: "-webkit-box",
                WebkitLineClamp: 10,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }}
            >
              {cur.abstract}
            </div>
          </div>

          <div
            style={{
              padding: 16,
              borderTop: "1px solid #f0f0f0",
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
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid #ddd",
                  opacity: likeDisabled ? 0.6 : 1,
                  fontWeight: 800,
                  cursor: likeDisabled ? "not-allowed" : "pointer",
                  background: liked ? "rgba(255,0,0,0.08)" : "white",
                }}
              >
                {liked ? "❤️ Liked" : "🤍 Like"}
              </button>

              <button
                onClick={() => onToggle("bookmark")}
                disabled={bmDisabled}
                aria-pressed={bookmarked}
                style={{
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid #ddd",
                  opacity: bmDisabled ? 0.6 : 1,
                  fontWeight: 800,
                  cursor: bmDisabled ? "not-allowed" : "pointer",
                  background: bookmarked ? "rgba(0,0,0,0.06)" : "white",
                }}
              >
                {bookmarked ? "🔖 Bookmarked" : "📑 Bookmark"}
              </button>

              <button
                onClick={onDetail}
                style={{
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid #ddd",
                  fontWeight: 900,
                  cursor: "pointer",
                  background: "white",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 6
                }}
              ><ExternalLink size={14} style={{ verticalAlign: "middle", marginLeft: 6 }} />
                자세히 보기 
              </button>
            </div>

            <div style={{ opacity: 0.6, fontSize: 12 }}>키보드: ↑ 이전 / ↓ 다음 / Space 일시정지</div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10, alignItems: "stretch" }}>
          <button
            onClick={goPrev}
            style={{
              height: 46,
              borderRadius: 14,
              border: "1px solid #e5e5e5",
              background: "white",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
              boxShadow: "0 6px 16px rgba(0,0,0,0.06)",
              color: 'black'
            }}
            title="이전 (↑)"
          >
            <ChevronUp />
          </button>

          <button
            onClick={goNext}
            style={{
              height: 46,
              borderRadius: 14,
              border: "1px solid #e5e5e5",
              background: "white",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
              boxShadow: "0 6px 16px rgba(0,0,0,0.06)",
              color: 'black'
            }}
            title="다음 (↓)"
          >
            <ChevronDown />
          </button>

          <button
            onClick={togglePause}
            style={{
              height: 46,
              borderRadius: 14,
              border: "1px solid #e5e5e5",
              background: paused ? "rgba(0,0,0,0.06)" : "white",
              cursor: "pointer",
              display: "grid",
              placeItems: "center",
              boxShadow: "0 6px 16px rgba(0,0,0,0.06)",
            }}
            title="일시정지/재생 (Space)"
          >
            {paused ? <Play color="white" /> : <Pause color="black"/>}
          </button>
        </div>
      </div>
    </div>
  );
}
