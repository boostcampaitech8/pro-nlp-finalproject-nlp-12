// src/pages/ShortsFeedPage.jsx
import { useEffect, useRef, useState, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom"; 
import { getFeed } from "../api/feed";
import { searchPapers } from "../api/search"; 
import ShortsCard from "../components/ShortsCard";
import "../styles/shorts.css";
import { getUserId } from "../utils/userId";

export default function ShortsFeedPage() {
  const navigate = useNavigate();
  const location = useLocation(); 

  const [userId] = useState(() => getUserId());
  const [limit, setLimit] = useState(20);

  const [items, setItems] = useState([]);
  const [idx, setIdx] = useState(0);

  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);

  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [err, setErr] = useState(null);

  const viewRef = useRef(null);
  const [pageH, setPageH] = useState(window.innerHeight);

  const wheelLockRef = useRef(false);
  const clamp = (n, len) => Math.max(0, Math.min(n, Math.max(0, len - 1)));

  // 검색 상태
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("feed"); // "feed" | "search"


  // 10초 자동 넘김 + 진행바 + 일시정지
  const AUTO_MS = 5_000;
  const [isPaused, setIsPaused] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const rafRef = useRef(null);
  const lastTsRef = useRef(null);

  const resetTimer = useCallback(() => {
    setElapsedMs(0);
    lastTsRef.current = null;
  }, []);

  // userId 없으면 즉시 onboarding으로
  useEffect(() => {
    if (!userId) {
      navigate("/onboarding", { replace: true });
    }
  }, [userId, navigate]);

  useEffect(() => {
    const calc = () => {
      const h = viewRef.current?.clientHeight ?? window.innerHeight;
      setPageH(h);
    };
    calc();
    window.addEventListener("resize", calc);
    return () => window.removeEventListener("resize", calc);
  }, []);

  const loadFirst = async () => {
    if (!userId) return; // userId 없으면 요청 금지

    setLoading(true);
    setErr(null);
    try {
      const data = await getFeed({ userId, limit, cursor: null });

      setItems(data.items ?? []);
      setIdx(0);
      setNextCursor(data.next_cursor ?? null);
      setHasMore(Boolean(data.has_more));

      setMode("feed"); // feed 모드로 유지
      resetTimer();
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  const loadMore = async () => {
    if (!userId) return;
    if (mode !== "feed") return; // 검색 중이면 feed pagination 금지
    if (!hasMore) return;
    if (!nextCursor) return;
    if (loadingMore) return;

    setLoadingMore(true);
    setErr(null);
    try {
      const data = await getFeed({ userId, limit, cursor: nextCursor });
      const newItems = data.items ?? [];

      setItems((prev) => {
        const seen = new Set(prev.map((x) => x.paper_id));
        const merged = [...prev];
        for (const it of newItems) {
          if (!seen.has(it.paper_id)) merged.push(it);
        }
        return merged;
      });

      setNextCursor(data.next_cursor ?? null);
      setHasMore(Boolean(data.has_more));
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoadingMore(false);
    }
  };

  // 검색 실행
  const runSearch = async (q) => {
    if (!userId) return;
    const qq = String(q ?? "").trim();
    if (!qq) return;

    setLoading(true);
    setErr(null);

    try {
      const data = await searchPapers({ userId, q: qq, k: limit });

      setItems(data.items ?? []);
      setIdx(0);

      // 🔴 feed 전용 상태 끄기(검색 결과는 cursor 없음)
      setNextCursor(null);
      setHasMore(false);

      setMode("search");
      resetTimer();
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  // 검색 해제(피드로 복귀)
  const clearSearch = async () => {
    setQuery("");
    setMode("feed");
    await loadFirst();
    resetTimer();
  };

  // 초기 로드: userId 있을 때만
  useEffect(() => {
    if (!userId) return;
    loadFirst();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // limit 바꾸면 새로 로드
  // - 검색 모드면: 같은 query로 재검색
  // - 피드 모드면: feed 재로드
  useEffect(() => {
    if (!userId) return;

    if (mode === "search") {
      const qq = query.trim();
      if (qq) runSearch(qq);
      else loadFirst();
      return;
    }

    loadFirst();
  }, [limit, userId]);

  // idx가 끝에 가까우면 loadMore (피드 모드에서만)
  useEffect(() => {
    if (mode !== "feed") return;
    const remaining = items.length - 1 - idx;
    if (remaining <= 2) loadMore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, items.length, hasMore, nextCursor, userId, mode]);

  const goNext = useCallback(() => {
    setIdx((prev) => clamp(prev + 1, items.length));
  }, [items.length]);

  const goPrev = useCallback(() => {
    setIdx((prev) => clamp(prev - 1, items.length));
  }, [items.length]);

  const goNextWithReset = useCallback(() => {
    goNext();
    resetTimer();
  }, [goNext, resetTimer]);

  const goPrevWithReset = useCallback(() => {
    goPrev();
    resetTimer();
  }, [goPrev, resetTimer]);

  const onWheel = (e) => {
    if (wheelLockRef.current) return;
    wheelLockRef.current = true;

    if (e.deltaY > 0) goNextWithReset();
    else goPrevWithReset();

    setTimeout(() => {
      wheelLockRef.current = false;
    }, 220);
  };

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "ArrowDown") goNextWithReset();
      if (e.key === "ArrowUp") goPrevWithReset();
      if (e.key === " " || e.code === "Space") {
        // 스페이스로 일시정지/재생 (원치 않으면 삭제)
        e.preventDefault();
        setIsPaused((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [goNextWithReset, goPrevWithReset]);

  // URL 기반 search 연결 (핵심)
  useEffect(() => {
    if (!userId) return;

    const params = new URLSearchParams(location.search);
    const m = params.get("mode");
    const q = params.get("q");

    if (m === "search" && q && String(q).trim()) {
      const qq = String(q).trim();

      // 같은 검색어로 이미 search 모드면 불필요 재호출 방지
      if (mode === "search" && query.trim() === qq) return;

      setQuery(qq);
      runSearch(qq);
      return;
    }

    // URL에 search가 없는데, 현재가 search 모드면 feed로 복귀(선택)
    if (mode === "search") {
      clearSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.search, userId]);

  // idx 바뀌면 타이머 리셋(카드 넘어갈 때마다 0초부터)
  useEffect(() => {
    resetTimer();
  }, [idx, resetTimer]);

  // 10초 자동 넘김 타이머 (수동 조작은 유지)
  useEffect(() => {
    // 아이템 없으면 굳이 돌리지 않기
    if (items.length === 0) return;

    // 마지막 카드에서 더 이상 못 넘기면(검색모드 or 피드이지만 더 없음) 타이머를 "꽉 찬 상태"로 유지
    const atEnd = idx >= items.length - 1;
    const canAdvance = !atEnd; // 현재 페이지의 아이템 범위 내에서만 자동 이동

    if (isPaused) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastTsRef.current = null;
      return;
    }

    // 끝인데 못 넘기면, 진행바 100%로 고정(원하면 여기서 자동 pause도 가능)
    if (!canAdvance) {
      setElapsedMs(AUTO_MS);
      return;
    }

    const loop = (ts) => {
      if (lastTsRef.current == null) lastTsRef.current = ts;
      const dt = ts - lastTsRef.current;
      lastTsRef.current = ts;

      setElapsedMs((prev) => {
        const next = prev + dt;
        if (next >= AUTO_MS) {
          goNext(); // 자동 다음 카드
          return 0;
        }
        return next;
      });

      rafRef.current = requestAnimationFrame(loop);
    };

    rafRef.current = requestAnimationFrame(loop);

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      lastTsRef.current = null;
    };
  }, [isPaused, items.length, idx, goNext]);

  // userId 없으면 렌더 자체를 막아서 깜빡임/에러 방지
  if (!userId) return null;

  const progressPct = Math.min(100, (elapsedMs / AUTO_MS) * 100);

  return (
    <div className="shorts-root" onWheel={onWheel}>
      <div className="shorts-header">
        {/* 서비스명 변경 */}
        <div className="shorts-logo">10seconds</div>

        {/* (현재는 여전히 상단 검색창 존재)
            네 목표가 "Search 탭에서만 검색창"이면
            이 form을 제거하고, SearchPage에서 /recommend?mode=search&q=... 로 보내면 됨 */}
        <form
          className="shorts-search"
          onSubmit={(e) => {
            e.preventDefault();
            const qq = query.trim();
            if (!qq) return;
            runSearch(qq);
            resetTimer();
          }}
        >
          <input
            className="shorts-search-input"
            placeholder="논문 검색 (예: RAG, multi-agent, LoRA)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />

          {mode === "search" ? (
            <button
              type="button"
              className="shorts-search-btn ghost"
              onClick={clearSearch}
              title="검색 해제"
            >
              ✕
            </button>
          ) : null}

          <button type="submit" className="shorts-search-btn">
            검색
          </button>
        </form>
      </div>

      {err && <div className="shorts-error">{err}</div>}

      <div className="shorts-view" ref={viewRef}>
        {items.length > 0 ? (
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
          <div className="shorts-empty">{loading ? "Loading..." : "No items"}</div>
        )}
      </div>

      <div className="shorts-nav">
        <button
          className="shorts-nav-btn"
          onClick={goPrevWithReset}
          disabled={idx === 0}
        >
          ▲
        </button>
        <button
          className="shorts-nav-btn"
          onClick={goNextWithReset}
          disabled={
            items.length === 0 ||
            (idx === items.length - 1 && mode === "feed" && !hasMore)
          }
          title={
            mode === "feed" && !hasMore && idx === items.length - 1
              ? "No more items"
              : ""
          }
        >
          ▼
        </button>
      </div>

      {/* ⏱ 진행바: feed 페이지와 bottom nav 경계(바로 위)에 표시 */}
      <div className="shorts-progress">
        <div
          className="shorts-progress__fill"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* ⏸ 일시정지 / 재생 */}
      <button
        className="shorts-pause-btn"
        onClick={() => setIsPaused((v) => !v)}
        title={isPaused ? "재생" : "일시정지"}
      >
        {isPaused ? "▶" : "⏸"}
      </button>

      {/* 상태 문구: 피드 모드에서만 더보기 표시 */}
      {mode === "feed" && (loadingMore || (idx >= items.length - 1 && hasMore)) && (
        <div className="shorts-status">
          {loadingMore ? "Loading more..." : "More available"}
        </div>
      )}
    </div>
  );
}
