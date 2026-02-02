"""Rate Limiter - API 요청 제한"""
from datetime import datetime, timedelta
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# In-memory storage (MVP용, 나중에 Redis로 교체 가능)
_request_timestamps: dict[str, dict[str, list[datetime]]] = {}


def check_rate_limit(
    user_id: str,
    action: str,
    max_requests: int = 2,
    window_minutes: int = 1,
) -> bool:
    """
    Rate limit 체크

    Args:
        user_id: 유저 식별자
        action: 액션 이름 (예: "survey", "feed")
        max_requests: 윈도우 내 최대 요청 수
        window_minutes: 시간 윈도우 (분)

    Returns:
        True if allowed, raises HTTPException if rate limited
    """
    now = datetime.now()
    window = timedelta(minutes=window_minutes)

    # 유저별, 액션별 기록 초기화
    if user_id not in _request_timestamps:
        _request_timestamps[user_id] = {}
    if action not in _request_timestamps[user_id]:
        _request_timestamps[user_id][action] = []

    # 윈도우 내 요청만 유지
    _request_timestamps[user_id][action] = [
        ts for ts in _request_timestamps[user_id][action]
        if now - ts < window
    ]

    # 제한 체크
    if len(_request_timestamps[user_id][action]) >= max_requests:
        logger.warning(f"Rate limit exceeded: user={user_id}, action={action}")
        raise HTTPException(
            status_code=429,
            detail=f"요청이 너무 많습니다. {window_minutes}분에 {max_requests}회까지 가능합니다."
        )

    # 요청 기록
    _request_timestamps[user_id][action].append(now)
    return True


def clear_rate_limit(user_id: str = None, action: str = None):
    """Rate limit 기록 초기화 (테스트용)"""
    global _request_timestamps

    if user_id is None:
        _request_timestamps = {}
    elif action is None:
        _request_timestamps.pop(user_id, None)
    else:
        if user_id in _request_timestamps:
            _request_timestamps[user_id].pop(action, None)
