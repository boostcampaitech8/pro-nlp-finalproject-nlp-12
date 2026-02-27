from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
import asyncio

class PaperSummary(BaseModel):
    motivation: str = Field(description="연구 배경 및 문제 의식")
    methodology: str = Field(description="주요 방법론")
    performance: str = Field(description="실험 및 성과")
    significance: str = Field(description="의의 및 향후 영향력")
    keypoint: str = Field(description="핵심 요약")

class SummarizeService:
    """
    요약 및 번역을 수행
    통상적으로 영어는 1토큰당 4글자, 한국어는 1토큰당 1글자.
    분기가 되는 토큰 수 계산 기준: 32k(입력 한계) - 4k(출력 한계) - 2k (여유분) = 26k
    """
    def __init__(self, clova_client):
        self.clova_client = clova_client

        # 안전하게 26000 토큰 이내면 한 번에 처리
        self.MAX_ONE_SHOT_TOKENS = 26000

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=20000, # 문맥 보존 극대화, API 호출 최소화를 위해
            chunk_overlap=2000, # 10%를 중첩하여 문맥이 끊기는 것을 방지
            length_function=self.clova_client.llm.get_num_tokens, # 토큰 수 계산 함수를 length로 설정
            separators=["\n\n", "\n", ". ", " ", ""] # 문단, 줄바꿈, 문장, 공백/단어, 글자 우선순위
        )

        # TPM(80000)을 초과하지 않도록 하기 위해 안전하게 설정.
        self.semaphore = asyncio.Semaphore(3)

        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()

    async def summarize(self, text: str) -> str:
        # 1. 토큰 수 계산 (llm 객체의 메서드 활용)
        try:
            num_tokens = self.clova_client.llm.get_num_tokens(text)
        except Exception as e:
            # 토큰 계산 실패 시, 영어 4글자=1토큰 기준으로 추산.
            num_tokens = len(text) // 4

        print(f"[Analysis] 입력 텍스트 토큰 수: {num_tokens} (길이: {len(text)})")

        # ------------------------------------------------------------------
        # 분기 1: 토큰 수가 26000 이하이면 -> Stuff
        # ------------------------------------------------------------------        
        if num_tokens <= self.MAX_ONE_SHOT_TOKENS:
            print(f"[Fast Track] 토큰 수가 허용 범위 내입니다. 즉시 요약합니다.")
            return await self.clova_client.run_prompt("full_prompt", {"text": text}, self.json_parser)
        
        # ------------------------------------------------------------------
        # 분기 2: 토큰 수가 26000 초과이면 -> Map-Reduce
        # ------------------------------------------------------------------
        print(f"[Map-Reduce] Chunk 단위 병렬 처리를 시작합니다.")

        # Chunk 단위로 쪼개기(길이를 token 기준으로 했으므로 20000 토큰 단위로 분할)
        chunks = self.splitter.split_text(text)
        print(f"Chunk 개수: {len(chunks)}개")

        async def chunk_summarize(chunk_text):
            async with self.semaphore:
                chunk_summary = await self.clova_client.run_prompt("map_prompt", {"text": chunk_text}, self.str_parser)
                
                if not chunk_summary:
                    print(f"Warning: Chunk summary failed for text starting with: {chunk_text[:30]}...")

                return chunk_summary
            
        # Map 수행
        map_results = await asyncio.gather(*[chunk_summarize(c) for c in chunks])
        combined_summaries = "\n\n".join(map_results)

        # Reduce 수행
        return await self.clova_client.run_prompt("reduce_prompt", {"text": combined_summaries}, self.json_parser)