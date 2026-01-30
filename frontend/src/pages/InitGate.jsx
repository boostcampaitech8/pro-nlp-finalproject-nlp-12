import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getOrCreateUserId } from "../utils/userId";
import { ensureUser } from "../api/users";

export default function InitGate() {
  const nav = useNavigate();
  const [err, setErr] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const uid = getOrCreateUserId();
        const out = await ensureUser(uid); // { user_id, has_onboarded }
        if (out?.has_onboarded) nav("/shorts", { replace: true });
        else nav("/onboarding", { replace: true });
      } catch (e) {
        console.error(e);
        setErr(String(e?.message || e));
      }
    })();
  }, [nav]);

  if (err) {
    return (
      <div style={{ padding: 20 }}>
        <h3>초기화 실패</h3>
        <p style={{ opacity: 0.8 }}>{err}</p>
        <p style={{ opacity: 0.7 }}>
          백엔드(127.0.0.1:8000)가 켜져 있고, CORS가 설정됐는지 확인해줘.
        </p>
      </div>
    );
  }

  return <div style={{ padding: 20 }}>Loading...</div>;
}
