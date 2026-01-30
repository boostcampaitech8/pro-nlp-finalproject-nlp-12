import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createAndStoreUserId } from "../utils/userId";
import { ensureUser, saveOnboarding } from "../api/users";

export default function OnboardingPage() {
  const nav = useNavigate();
  const [topics, setTopics] = useState([]);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState(null);

  const submit = async () => {
    setSaving(true);
    setErr(null);
    try {
      // 설문 완료 시점에만 userId 생성 + localStorage 저장
      const userId = createAndStoreUserId();

      // 백엔드에 유저 생성/확인
      await ensureUser(userId);

      // 설문 저장
      await saveOnboarding(userId, topics);

      nav("/feed", { replace: true });
    } catch (e) {
      setErr(String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Onboarding</h2>

      <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button onClick={() => setTopics(["cs.CL"])}>cs.CL</button>
        <button onClick={() => setTopics(["cs.LG"])}>cs.LG</button>
        <button onClick={() => setTopics(["cs.AI"])}>cs.AI</button>
      </div>

      <div style={{ marginTop: 12 }}>
        <div>selected: {JSON.stringify(topics)}</div>
      </div>

      {err && <div style={{ color: "crimson", marginTop: 12 }}>{err}</div>}

      <div style={{ marginTop: 16 }}>
        <button onClick={submit} disabled={saving || topics.length === 0}>
          {saving ? "Saving..." : "Start"}
        </button>
      </div>
    </div>
  );
}
