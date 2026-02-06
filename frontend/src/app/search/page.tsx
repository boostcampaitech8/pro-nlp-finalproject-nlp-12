"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { FeedItem, searchFeed } from "../../lib/api";
import { getUserId } from "../../lib/user";
import ShortFormSection from "../../components/feed/ShortFormSection";

export default function SearchPage() {
  const searchParams = useSearchParams();
  const queryParam = searchParams?.get("q") ?? "";
  const queryLabel = useMemo(() => queryParam.trim(), [queryParam]);

  const [q, setQ] = useState(queryParam);
  const [items, setItems] = useState<FeedItem[] | null>(null);
  const [view, setView] = useState<"papers" | "timeline">("papers");

  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const runSearch = useCallback(
    async (cursor: string | null, term: string) => {
      const uid = getUserId();
      if (!uid) return;

      const out = await searchFeed(uid, term.trim());

      const newItems = Array.isArray(out) ? out : [];

      setItems((prev) => (cursor ? [...(prev ?? []), ...newItems] : newItems));
      setNextCursor(null);
      setHasMore(false);
    },
    []
  );

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;

    setLoading(true);
    setErr(null);

    try {
      await runSearch(null, q);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const nextQuery = queryParam.trim();
    setQ(queryParam);
    setView("papers");

    if (!nextQuery) {
      setItems(null);
      setErr(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setErr(null);

    (async () => {
      try {
        await runSearch(null, nextQuery);
      } catch (e: any) {
        if (!cancelled) {
          setErr(String(e?.message ?? e));
          setItems([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [queryParam, runSearch]);

  const fetchMore = useCallback(async () => {
    if (!hasMore || loadingMore || !nextCursor) return;
    setLoadingMore(true);
    try {
      await runSearch(nextCursor, q);
    } catch (e: any) {
      setErr(String(e?.message ?? e));
    } finally {
      setLoadingMore(false);
    }
  }, [hasMore, loadingMore, nextCursor, runSearch, q]);

  if (items === null) {
    return (
      <div style={{ padding: 24, display: "grid", placeItems: "center", minHeight: "70dvh" }}>
        <div
          style={{
            width: "min(720px, 100%)",
            padding: 20,
            borderRadius: 20,
            background: "rgba(255,255,255,0.9)",
            border: "1px solid rgba(17, 18, 24, 0.08)",
            boxShadow: "0 18px 50px rgba(17, 18, 24, 0.16)",
            backdropFilter: "blur(12px)",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em", color: "#111218" }}>
            Search
          </div>
          <div style={{ marginTop: 10, color: "rgba(17, 18, 24, 0.7)" }}>
            Use the search bar at the top to find papers and topics.
          </div>
          {loading && <div style={{ marginTop: 12, fontWeight: 600 }}>Searching...</div>}
        </div>
        {err && <div style={{ marginTop: 12, color: "crimson" }}>{err}</div>}
      </div>
    );
  }

  const showViewToggle = Boolean(queryLabel);

  return (
    <>
      {showViewToggle && (
        <div
          style={{
            width: "min(960px, 100%)",
            margin: "16px auto 0",
            padding: "0 16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 12,
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: 4,
              borderRadius: 999,
              border: "1px solid rgba(17, 18, 24, 0.12)",
              background: "rgba(255, 255, 255, 0.85)",
            }}
          >
            <button
              onClick={() => setView("papers")}
              style={{
                padding: "4px 10px",
                borderRadius: 999,
                border: "none",
                fontWeight: 700,
                cursor: "pointer",
                background: view === "papers" ? "rgba(255, 107, 0, 0.16)" : "transparent",
                color: "#111218",
                fontSize: 12,
              }}
            >
              Papers
            </button>
            <button
              onClick={() => setView("timeline")}
              style={{
                padding: "4px 10px",
                borderRadius: 999,
                border: "none",
                fontWeight: 700,
                cursor: "pointer",
                background: view === "timeline" ? "rgba(17, 18, 24, 0.08)" : "transparent",
                color: "#111218",
                fontSize: 12,
              }}
            >
              Timeline
            </button>
          </div>
        </div>
      )}

      {view === "papers" ? (
        <>
          <ShortFormSection items={items} onNeedMore={fetchMore} />
          {loadingMore && <div style={{ padding: 12, opacity: 0.6 }}>Loading more results...</div>}
          {err && <div style={{ padding: 12, color: "crimson" }}>{err}</div>}
        </>
      ) : (
        <div style={{ padding: 24, display: "grid", placeItems: "center", minHeight: "70dvh" }}>
          <div
            style={{
              width: "min(720px, 100%)",
              padding: 24,
              borderRadius: 22,
              background: "rgba(255,255,255,0.9)",
              border: "1px solid rgba(17, 18, 24, 0.08)",
              boxShadow: "0 18px 50px rgba(17, 18, 24, 0.16)",
              backdropFilter: "blur(12px)",
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: "-0.02em", color: "#111218" }}>
              {queryLabel} — Research Timeline
            </div>
            <div
              style={{
                marginTop: 16,
                height: 180,
                borderRadius: 16,
                background:
                  "linear-gradient(135deg, rgba(255,107,0,0.15) 0%, rgba(255,45,85,0.18) 45%, rgba(0,194,168,0.18) 100%)",
                border: "1px dashed rgba(17, 18, 24, 0.18)",
                display: "grid",
                placeItems: "center",
                color: "#2c2f3a",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Timeline graph placeholder
            </div>
          </div>
        </div>
      )}
    </>
  );
}
