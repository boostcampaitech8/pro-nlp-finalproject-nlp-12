from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
import asyncio

class PaperSummary(BaseModel):
    motivation: str = Field(description="연구 배경 및 문제 의식")
    methodology: str = Field(description="주요 방법론")
    performance: str = Field(description="실험 및 성과")
    significance: str = Field(description="의의 및 향후 영향력")

class SummarizeService:
    def __init__(self, clova_client):
        self.clova_client = clova_client

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=400,
            separators=["\n\n", "\n", " ", ""]
        )

        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()

    async def summarize(self, text: str) -> str:
        """
        요약 및 번역을 수행합니다.
        """
        # 청크 단위로 쪼개기
        chunks = self.splitter.split_text(text)

        # 세마포어 설정
        semaphore = asyncio.Semaphore(3)

        async def chunk_summarize(chunk_text):
            async with semaphore:
                chunk_summary = await self.clova_client.run_prompt("map_prompt", {"text": chunk_text}, self.str_parser)
                
                if not chunk_summary:
                    print(f"Warning: Chunk summary failed for text starting with: {chunk_text[:30]}...")

                await asyncio.sleep(1)
                return chunk_summary

        map_tasks = [chunk_summarize(chunk_text=chunk) for chunk in chunks]

        # 모든 청크를 동시에 요약
        map_results = await asyncio.gather(*map_tasks)

        # 요약된 결과를 하나로 합쳐서 최종 요약
        combined_summaries = "\n\n".join(map_results)

        final_summary = await self.clova_client.run_prompt(
            "reduce_prompt",
            {"text": combined_summaries},
            self.json_parser
        )

        return final_summary