export const USER_ID_KEY = "user_id";

export function getUserId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(USER_ID_KEY);
}

export function setUserId(uid: string) {
  localStorage.setItem(USER_ID_KEY, uid);
}

export function ensureUserId(): string {
  const existing = getUserId();
  if (existing) return existing;

  const uid = crypto.randomUUID();
  setUserId(uid);
  return uid;
}
