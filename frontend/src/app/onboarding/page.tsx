"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ensureUserId } from "../../lib/user";

export default function OnboardingPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    setSubmitting(true);

    // TODO: onboarding 결과 backend로 보내기

    // 성공 시 user_id 생성/저장
    ensureUserId();

    router.replace("/home");
  }

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ fontSize: 22, fontWeight: 900 }}>Onboarding</h1>
      <p style={{ opacity: 0.75 }}>간단한 설문으로 cold start를 줄여요.</p>

      {/*TODO 설문 UI는 여기에 구현 */}
      <button onClick={submit} disabled={submitting} style={{ marginTop: 16 }}>
        {submitting ? "처리중..." : "설문 제출"}
      </button>
    </div>
  );
}
