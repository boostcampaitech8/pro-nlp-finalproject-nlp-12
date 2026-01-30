export async function postEvent({ userId, paperId, eventType }) {
  const res = await fetch("/api/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      paper_id: paperId,
      event_type: eventType,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`POST /events -> ${res.status}\n${text}`);
  }

  return res.json(); // { ok: true, active?: boolean }
}
