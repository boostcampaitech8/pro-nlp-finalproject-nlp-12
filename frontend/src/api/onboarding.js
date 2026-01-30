export async function upsertOnboarding({ userId, onboarding }) {
  const res = await fetch(`/api/profiles/onboarding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      onboarding_json: onboarding,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`onboarding failed: ${res.status} ${text}`);
  }

  return res.json().catch(() => ({}));
}
