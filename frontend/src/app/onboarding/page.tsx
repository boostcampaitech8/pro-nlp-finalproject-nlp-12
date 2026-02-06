"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { postOnboarding } from "../../lib/api";
import { ensureUserId } from "../../lib/user";

const CATEGORIES = [
  { value: "cs.LG", label: "Machine Learning", desc: "모델이 스스로 학습" },
  { value: "cs.CL", label: "NLP", desc: "언어 이해와 생성" },
  { value: "cs.AI", label: "Artificial Intelligence", desc: "지능형 시스템" },
  { value: "cs.CV", label: "Computer Vision", desc: "이미지/비디오" },
  { value: "cs.SI", label: "Social & Info Networks", desc: "네트워크 분석" },
  { value: "stat.ML", label: "Statistical ML", desc: "통계적 학습" },
  { value: "cs.IR", label: "Information Retrieval", desc: "검색과 랭킹" },
  { value: "cs.CY", label: "Computers & Society", desc: "사회적 영향" },
  { value: "physics.soc-ph", label: "Social Physics", desc: "사회 현상 모델" },
  { value: "cs.NE", label: "Neural & Evolutionary", desc: "신경망/진화" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

  const selectedSet = useMemo(() => new Set(selected), [selected]);

  async function submit() {
    if (selected.length === 0) return;
    setSubmitting(true);

    const uid = ensureUserId();
    await postOnboarding({ user_id: uid, categories: selected });

    router.replace("/home");
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "radial-gradient(1200px 600px at 80% -10%, #f4f1ff 0%, #f9fbff 35%, #f7f7fb 60%, #f4f7f2 100%)",
        color: "#111218",
        fontFamily: "'Space Grotesk', 'DM Sans', 'Noto Sans KR', sans-serif",
      }}
    >
      <div style={{ maxWidth: 980, margin: "0 auto", padding: "48px 20px 72px" }}>
        <div style={{ marginTop: 12 }}>
          <h1 style={{ fontSize: 36, lineHeight: 1.1, margin: 0, fontWeight: 800 }}>
            관심 분야를 골라주세요
          </h1>
          <p style={{ marginTop: 10, fontSize: 15, opacity: 0.75 }}>
            선택한 분야를 기준으로 개인화된 피드를 바로 시작합니다.
          </p>
        </div>

        <div
          style={{
            marginTop: 28,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 12,
          }}
        >
          {CATEGORIES.map((c) => {
            const active = selectedSet.has(c.value);
            return (
              <button
                key={c.value}
                onClick={() =>
                  setSelected((prev) =>
                    prev.includes(c.value)
                      ? prev.filter((x) => x !== c.value)
                      : [...prev, c.value]
                  )
                }
                style={{
                  padding: "16px 16px 14px",
                  borderRadius: 16,
                  border: active ? "2px solid #111218" : "1px solid rgba(17,18,24,0.12)",
                  background: active
                    ? "linear-gradient(180deg, rgba(17,18,24,0.06) 0%, rgba(17,18,24,0.02) 100%)"
                    : "white",
                  boxShadow: active
                    ? "0 6px 18px rgba(17,18,24,0.12)"
                    : "0 6px 18px rgba(17,18,24,0.06)",
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "transform 120ms ease, box-shadow 120ms ease, border 120ms ease",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ fontSize: 16, fontWeight: 800 }}>{c.label}</div>
                  <div
                    style={{
                      width: 18,
                      height: 18,
                      borderRadius: 999,
                      border: active ? "6px solid #111218" : "1px solid rgba(17,18,24,0.2)",
                    }}
                  />
                </div>
                <div style={{ marginTop: 6, fontSize: 12, color: "#6b7280" }}>{c.desc}</div>
              </button>
            );
          })}
        </div>

        <div style={{ marginTop: 22, display: "flex", alignItems: "center", gap: 12 }}>
          <button
            onClick={submit}
            disabled={submitting || selected.length === 0}
            style={{
              padding: "12px 18px",
              borderRadius: 12,
              border: "none",
              background:
                submitting || selected.length === 0
                  ? "#e5e7eb"
                  : "linear-gradient(135deg, #111218 0%, #2b2f3a 100%)",
              color: submitting || selected.length === 0 ? "#9ca3af" : "white",
              fontWeight: 800,
              cursor: submitting || selected.length === 0 ? "not-allowed" : "pointer",
            }}
          >
            {submitting ? "처리중.." : `선택 완료 (${selected.length})`}
          </button>
          <div style={{ fontSize: 12, opacity: 0.6 }}>
            최소 1개 선택
          </div>
        </div>
      </div>
    </div>
  );
}
