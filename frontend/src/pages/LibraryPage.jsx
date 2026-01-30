// src/pages/LibraryPage.jsx
import { useEffect, useMemo, useState } from "react";
import { fetchMyLibrary } from "../api/library";
import "../styles/library.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";

const USER_ID_KEY = "paper_shorts_user_id";

function Tab({ active, children, onClick }) {
  return (
    <button className={`lib-tab ${active ? "active" : ""}`} onClick={onClick}>
      {children}
    </button>
  );
}

function trimText(s, n = 240) {
  if (!s) return "";
  return s.length > n ? s.slice(0, n) + "…" : s;
}

export default function LibraryPage() {
  const [userId, setUserId] = useState(() => {
    const saved = localStorage.getItem(USER_ID_KEY);
    return saved && saved.trim() ? saved.trim() : "u1";
  });

  const [type, setType] = useState("all"); // all | like | bookmark
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [data, setData] = useState(null);

  // userId 변경 시 localStorage에도 저장
  useEffect(() => {
    if (userId && userId.trim()) {
      localStorage.setItem(USER_ID_KEY, userId.trim());
    }
  }, [userId]);

  // 라이브러리 조회
  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr("");

    fetchMyLibrary({ baseUrl: API_BASE, userId, type, limit: 100, offset: 0 })
      .then((json) => {
        if (!alive) return;
        setData(json);
      })
      .catch((e) => {
        if (!alive) return;
        setErr(e.message || String(e));
      })
      .finally(() => {
        if (!alive) return;
        setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [userId, type]);

  const items = data?.items || [];

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((it) => {
      const t = (it.title || "").toLowerCase();
      const a = (it.abstract || "").toLowerCase();
      return t.includes(needle) || a.includes(needle);
    });
  }, [items, q]);

  return (
    <div className="lib-wrap">
      <div className="lib-header">
        <div>
          <div className="lib-title">내 라이브러리</div>
          <div className="lib-sub">좋아요 / 북마크한 논문을 모아봐요</div>
        </div>

        <div className="lib-controls">
          <label className="lib-field">
            <span>user</span>
            <input value={userId} onChange={(e) => setUserId(e.target.value)} />
          </label>

          <label className="lib-field">
            <span>search</span>
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="title / abstract"
            />
          </label>
        </div>
      </div>

      <div className="lib-tabs">
        <Tab active={type === "all"} onClick={() => setType("all")}>
          All
        </Tab>
        <Tab active={type === "like"} onClick={() => setType("like")}>
          Likes
        </Tab>
        <Tab active={type === "bookmark"} onClick={() => setType("bookmark")}>
          Bookmarks
        </Tab>

        <div className="lib-count">
          {loading ? "Loading..." : `${filtered.length} items`}
        </div>
      </div>

      {err && <div className="lib-error">⚠️ {err}</div>}

      {!loading && !err && filtered.length === 0 && (
        <div className="lib-empty">
          아직{" "}
          {type === "like"
            ? "좋아요"
            : type === "bookmark"
              ? "북마크"
              : ""}{" "}
          한 논문이 없어요.
        </div>
      )}

      <div className="lib-grid">
        {filtered.map((it) => (
          <div
            key={`${it.event_type}-${it.paper_id}-${it.created_at}`}
            className="lib-card"
          >
            <div className="lib-badge-row">
              <span className={`lib-badge ${it.event_type}`}>
                {it.event_type === "like" ? "LIKE" : "BOOKMARK"}
              </span>
              <span className="lib-date">
                {new Date(it.created_at).toLocaleString()}
              </span>
            </div>

            <div className="lib-card-title">
              {it.title || `(paper_id=${it.paper_id})`}
            </div>

            {it.authors && <div className="lib-authors">{it.authors}</div>}

            {it.published_at && (
              <div className="lib-pub">
                published: {new Date(it.published_at).toLocaleDateString()}
              </div>
            )}

            {it.abstract && (
              <div className="lib-abs">{trimText(it.abstract)}</div>
            )}

            <div className="lib-actions">
              {it.abs_url && (
                <a
                  className="lib-btn"
                  href={it.abs_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  arXiv
                </a>
              )}
              {it.pdf_url && (
                <a
                  className="lib-btn"
                  href={it.pdf_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  PDF
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
