export async function ensureUser(userId) {
  const res = await fetch(`/api/users/ensure`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId }),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`ensureUser failed: ${res.status} ${txt}`);
  }
  return await res.json();
}

export async function saveOnboarding(userId, topics) {
  const res = await fetch(`/api/users/onboarding`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, answers: { topics } }),
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`saveOnboarding failed: ${res.status} ${txt}`);
  }
  return await res.json();
}
