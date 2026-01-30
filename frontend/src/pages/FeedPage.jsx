import { useEffect, useState } from "react";
import { getFeed } from "../api/feed";
import PaperCard from "../components/PaperCard";

export default function FeedPage() {
  const [userId, setUserId] = useState("u1");
  const [k, setK] = useState(5);

  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setErr(null);
    try {
      const json = await getFeed({ userId, k });
      setData(json);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ padding: 20, maxWidth: 980, margin: "0 auto" }}>
      <h1 style={{ marginTop: 0 }}>Feed</h1>

      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", marginBottom: 16 }}>
        <label>
          user_id:&nbsp;
          <input value={userId} onChange={(e) => setUserId(e.target.value)} />
        </label>

        <label>
          k:&nbsp;
          <input
            type="number"
            min={1}
            max={50}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            style={{ width: 80 }}
          />
        </label>

        <button onClick={load} disabled={loading}>
          {loading ? "Loading..." : "Reload"}
        </button>
      </div>

      {err && (
        <pre style={{ background: "#ffecec", border: "1px solid #ffb3b3", padding: 12, borderRadius: 8, whiteSpace: "pre-wrap" }}>
          {err}
        </pre>
      )}

      {!data && !err && loading && <div>Loading...</div>}

      {data && (
        <>
          <div style={{ color: "#666", marginBottom: 12 }}>
            user_id: <b>{data.user_id}</b> / k: <b>{data.k}</b> / items: <b>{data.items?.length ?? 0}</b>
          </div>

          {data.items?.map((item) => (
            <PaperCard key={item.paper_id} item={item} />
          ))}
        </>
      )}
    </div>
  );
}
