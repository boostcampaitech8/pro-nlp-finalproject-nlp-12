"""사용자 선호도 및 온보딩 서비스 (LLM 키워드 추출)"""
import json
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
import numpy as np

from src.entity.user import User
from src.client.embedder import embed_single, embed_texts
from src.config.settings import settings
from src.repository.paper_repository import PaperRepository
from src.repository.user_repository import UserRepository

logger = logging.getLogger(__name__)


class PreferenceService:
    """사용자 선호도 프로필 관리 및 LLM 키워드 추출"""

    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.user_repo = UserRepository(db)

    def save_onboarding(self, user_id: str, categories: List[str], paper_ids: List[int]) -> User:
        """
        온보딩 데이터 저장

        Args:
            user_id: 사용자 UUID
            categories: 선택한 카테고리 리스트
            paper_ids: 선택한 논문 ID 리스트

        Returns:
            업데이트된 User 엔티티
        """
        # 키워드 추출
        keywords = self.extract_keywords_from_papers(paper_ids)

        # 온보딩 데이터 구성
        onboarding_data = {
            "categories": categories,
            "paper_ids": paper_ids,
            "keywords": keywords,
        }

        # DB 저장
        return self.user_repo.set_onboarding(user_id, onboarding_data)

    def extract_keywords_from_papers(self, paper_ids: List[int]) -> List[str]:
        """
        선택한 논문들에서 LLM으로 키워드 추출

        Args:
            paper_ids: 논문 ID 리스트

        Returns:
            추출된 키워드 리스트
        """
        try:
            from groq import Groq

            papers = self.paper_repo.get_by_ids(paper_ids)
            if not papers:
                return []

            # 논문 정보를 텍스트로 조합 (최대 5개)
            papers_text = "\n".join([
                f"Title: {p.title}\nAbstract: {p.abstract or 'N/A'}\n"
                for p in papers[:5]
            ])

            client = Groq(api_key=settings.GROQ_API_KEY)

            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Extract 5-10 common research keywords from these papers.
Return ONLY a JSON object: {{"keywords": ["keyword1", "keyword2", ...]}}
All keywords MUST be in English. No other text.

{papers_text}"""
                    }
                ]
            )

            response_text = response.choices[0].message.content
            logger.debug(f"Groq response: {response_text}")

            # JSON 파싱 시도 1: {"keywords": [...]}
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    data = json.loads(json_str)
                    return data.get('keywords', [])
            except json.JSONDecodeError:
                pass

            # JSON 파싱 시도 2: [...] 배열 형식
            try:
                array_start = response_text.find('[')
                array_end = response_text.rfind(']') + 1
                if array_start >= 0 and array_end > array_start:
                    array_str = response_text[array_start:array_end]
                    return json.loads(array_str)
            except json.JSONDecodeError:
                pass

            return []

        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []

    def generate_preference_vector(
        self,
        user_id: str,
        categories: List[str],
        keywords: List[str]
    ) -> Optional[List[float]]:
        """
        Preference Query 텍스트 생성 및 임베딩

        Args:
            user_id: 사용자 UUID
            categories: 카테고리 리스트
            keywords: 키워드 리스트

        Returns:
            임베딩 벡터 (리스트 형태)
        """
        try:
            # Preference Query 텍스트 생성
            categories_text = ", ".join(categories) if categories else "general"
            keywords_text = ", ".join(keywords) if keywords else "research papers"

            preference_query = f"""
            Categories of interest: {categories_text}
            Research topics and keywords: {keywords_text}
            """

            # 임베딩 생성
            embedding = embed_single(preference_query)
            embedding_list = embedding.tolist()

            # DB에 벡터 저장 (선택적)
            self.user_repo.upsert_vector(user_id, json.dumps(embedding_list))

            return embedding_list

        except Exception as e:
            logger.error(f"Error generating preference vector: {e}")
            return None

    def get_profile(self, user_id: str) -> Optional[dict]:
        """사용자 프로필 조회"""
        user = self.user_repo.get_by_uuid(user_id)
        if not user:
            return None

        onboarding = user.onboarding_json or {}

        return {
            "user_id": user.uuid,
            "has_onboarded": user.has_onboarded or False,
            "categories": onboarding.get("categories", []),
            "paper_ids": onboarding.get("paper_ids", []),
            "keywords": onboarding.get("keywords", []),
            "has_vector": user.user_vector_json is not None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    def get_onboarding_papers(self, categories: List[str], limit: int = 20) -> List[dict]:
        """
        온보딩용 논문 후보 조회

        Args:
            categories: 선택한 카테고리
            limit: 반환할 논문 수

        Returns:
            논문 정보 리스트
        """
        papers = self.paper_repo.get_by_categories_with_citations(
            categories=categories,
            min_citations=5,
            limit=limit
        )

        ### 수정사항: 현재 Paper 엔티티에 맞게 필드 수정 (primary_category 제거)
        return [
            {
                "paper_id": p.id,
                "arxiv_id": p.arxiv_id,
                "title": p.title,
                "abstract": p.abstract,
                "citation_count": p.citation_count or 0,
            }
            for p in papers
        ]
