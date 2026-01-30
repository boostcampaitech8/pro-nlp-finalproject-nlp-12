import { useState } from "react";
import "../styles/searchPage.css";
import { getUserId } from "../utils/userId";
import { searchPapers } from "../api/search";
import ShortsViewer from "../components/ShortsViewer";

export default function SearchPage() {
  const [userId] = useState(() => getUserId());

  const [q, setQ] = useState("");
  const [submittedQ, setSubmittedQ] = useState("");
  const [items, setItems] = useState([]);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const runSearch = async (query) => {
    if (!userId) return;
    const qq = query.trim();
    if (!qq) return;

    setLoading(true);
    setErr(null);
    try {
      const data = await searchPapers({ userId, q: qq, k: 20 });
      setItems(data.items ?? []);
      setSubmittedQ(qq);
    } catch (e) {
      setErr(String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e) => {
    e.preventDefault();
    runSearch(q);
  };

  // 초기 화면: 입력창만
  if (!submittedQ && items.length === 0) {
    return (
      <div className="search-empty">
        <h2 className="search-empty__title">Search papers</h2>

        <form className="search-bar" onSubmit={onSubmit}>
          <input
            className="search-bar__input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="예: RAG, multi-agent, LoRA..."
          />
          <button className="search-bar__btn" type="submit" disabled={loading}>
            {loading ? "..." : "Search"}
          </button>
        </form>

        {err && <div className="search-error">{err}</div>}
      </div>
    );
  }

  // ✅ 검색 후: 상단에 검색바 + 아래는 recommend와 동일한 숏폼 UI
  return (
    <div>
      <div className="search-top">
        <form className="search-bar search-bar--top" onSubmit={onSubmit}>
          <input
            className="search-bar__input"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="다시 검색…"
          />
          <button className="search-bar__btn" type="submit" disabled={loading}>
            {loading ? "..." : "Search"}
          </button>
        </form>
        <div className="search-meta">
          {loading ? "검색 중..." : `“${submittedQ}” 결과: ${items.length}개`}
        </div>
      </div>

      <ShortsViewer
        items={items}
        userId={userId}
        loading={loading}
        err={err}
        hasMore={false}
      />
    </div>
  );
}
