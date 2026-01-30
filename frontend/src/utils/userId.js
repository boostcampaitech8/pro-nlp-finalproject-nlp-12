const KEY = "paper_shorts_user_id";

// 생성하지 않고 있는지만 확인
export function getUserId() {
  const v = localStorage.getItem(KEY);
  return v && v.trim().length > 0 ? v : null;
}

// 설문 완료 시점에만 호출해서 새 UUID 생성 + 저장
export function createAndStoreUserId() {
  // crypto.randomUUID() 지원 (최신 브라우저)
  const uuid = crypto.randomUUID();
  localStorage.setItem(KEY, uuid);
  return uuid;
}

// 기존 코드에서 setUserId를 쓰면 여기로 저장 */
export function setUserId(userId) {
  if (!userId || String(userId).trim().length === 0) {
    localStorage.removeItem(KEY);
    return null;
  }
  const v = String(userId).trim();
  localStorage.setItem(KEY, v);
  return v;
}

//  로그아웃/초기화 등에 사용
export function clearUserId() {
  localStorage.removeItem(KEY);
}
