from dotenv import load_dotenv
import os
from langchain_naver import ChatClovaX # langchain_naver 패키지 사용
from langchain_core.prompts import load_prompt

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type # Exponential Backoff

load_dotenv()

CLOVASTUDIO_API_KEY = os.getenv("CLOVASTUDIO_API_KEY")

# 재시도 시점에 실행될 콜백 함수 정의
def log_retry_attempt(retry_state):
    """
    retry_state.attempt_number: 현재 시도 횟수 (1부터 시작)
    retry_state.outcome: 발생한 예외 정보
    retry_state.next_action: 다음 대기 시간 정보
    """
    exception = retry_state.outcome.exception()
    print(f"⚠️ [재시도 경고] 시도 횟수: {retry_state.attempt_number}회 | 에러: {exception}")
    print(f"   ↳ {retry_state.next_action.sleep}초 대기 후 다시 시도")

def return_empty_on_failure(retry_state):
    """모든 재시도가 실패했을 때 빈 문자열을 반환하는 콜백 함수"""
    print(f"❌ [최종 실패] {retry_state.attempt_number}회 시도했으나 모두 실패했습니다. 빈 값을 반환합니다.")
    return ""

class ClovaClient:
    def __init__(self):
        self.llm = ChatClovaX(
            model="HCX-DASH-002",
            temperature=0.1, # 일관성을 원한다면 낮게 설정.
            max_tokens=2048,
            api_key=CLOVASTUDIO_API_KEY
        )

    @retry(
        # 1. 모든 Exception에 대해 재시도
        retry=retry_if_exception_type(Exception), 
        # 2. 최대 5번까지만 재시도
        stop=stop_after_attempt(5),      
        # 3. 지수 백오프: 2초 대기 -> 4초 -> 8초 ... (최대 10초)
        wait=wait_exponential(multiplier=2, min=2, max=10),
        before_sleep=log_retry_attempt,
        retry_error_callback=return_empty_on_failure
    )
    async def run_prompt(
        self,
        prompt_name: str,
        input_data: dict,
        output_parser
    ) -> str:
        """
        src/prompt 폴더에서 특정 YAML 파일을 읽어 LLM을 실행합니다.
        """
        prompt_path = os.path.join("src", "prompt", f"{prompt_name}.yaml")

        prompt_template = load_prompt(prompt_path, encoding="utf-8")

        chain = prompt_template | self.llm | output_parser
        return await chain.ainvoke(input_data)
