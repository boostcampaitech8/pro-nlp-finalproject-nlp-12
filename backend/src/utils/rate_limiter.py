"""Rate Limiter - API 요청 제한"""
from datetime import datetime, timedelta
from fastapi import HTTPException
import asyncio
import time
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


class RateLimiter:
    """
    비동기 Rate Limiter (외부 API 호출용)

    토큰 버킷 알고리즘을 사용하여 API 호출 속도를 제한합니다.
    """

    def __init__(self, max_calls: int, period: float):
        """
        Args:
            max_calls: 기간 내 최대 호출 수
            period: 기간 (초)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
        self.lock = asyncio.Lock()

    async def acquire(self):
        """호출 허가를 획득 (필요시 대기)"""
        async with self.lock:
            now = time.time()

            # 기간 밖의 오래된 호출 기록 제거
            self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

            # 제한에 도달했으면 대기
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    # 대기 후 다시 오래된 기록 제거
                    now = time.time()
                    self.calls = [call_time for call_time in self.calls if now - call_time < self.period]

            # 현재 호출 기록
            self.calls.append(now)
