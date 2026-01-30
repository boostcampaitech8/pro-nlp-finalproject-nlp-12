"""사용자 프로필 및 Preference 벡터 생성 서비스"""
import json
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
import numpy as np

from src.entity.user import User
from src.entity.paper import Paper
from src.service.embedder_service import embed_single, embed_texts
from src.config.settings import settings
from src.repository.paper_repository import PaperRepository
from src.repository.user_profile_repository import UserProfileRepository


class PreferenceService:
    """사용자 선호도 프로필 관리 및 벡터 생성"""
    
    def __init__(self, db: Session):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.profile_repo = UserProfileRepository(db)
    
    def save_categories(self, user_id: str, categories: list[str]):
        """Step 1: 사용자가 선택한 카테고리 저장"""
        profile_data = {
            "survey_categories": json.dumps(categories)
        }
        return self.profile_repo.create_or_update(user_id, profile_data)
    
    def save_papers(self, user_id: str, categories: list[str], paper_ids: list[int]):
        """Step 2: 사용자가 선택한 논문 저장"""
        profile_data = {
            "survey_categories": json.dumps(categories),
            "survey_paper_ids": json.dumps(paper_ids)
        }
        return self.profile_repo.create_or_update(user_id, profile_data)
    
    def extract_keywords_from_papers(self, paper_ids: list[int]) -> list[str]:
        """
        선택한 논문들에서 키워드 추출 (LLM 사용)
        
        Args:
            paper_ids: 선택한 논문 ID 리스트
            
        Returns:
            추출된 키워드 리스트
        """
        try:
            from groq import Groq
            
            # 논문 정보 조회
            papers = self.paper_repo.get_by_ids(paper_ids)
            
            if not papers:
                return []
            
            # 논문 정보를 텍스트로 조합
            papers_text = "\n".join([
                f"Title: {p.title}\nAbstract: {p.abstract or 'N/A'}\n"
                for p in papers[:5]  # 최대 5개만 사용
            ])
            
            # Groq LLM으로 키워드 추출
            client = Groq(api_key=settings.GROQ_API_KEY)
            
            message = client.messages.create(
                model=settings.GROQ_MODEL,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""다음 논문들의 공통 주제와 키워드를 5-10개 추출해주세요.
                        JSON 형식으로 "keywords": ["키워드1", "키워드2", ...] 형태로 응답해주세요.
                        
{papers_text}"""
                    }
                ]
            )
            
            # 응답 파싱
            response_text = message.content[0].text
            
            # JSON 부분 추출
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    data = json.loads(json_str)
                    return data.get('keywords', [])
            except json.JSONDecodeError:
                pass
            
            return []
        
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []
    
    def generate_preference_vector(
        self, 
        user_id: str, 
        categories: list[str], 
        paper_ids: list[int], 
        extracted_keywords: list[str]
    ) -> Optional[list[float]]:
        """
        사용자의 선호도 쿼리 벡터 생성 및 저장
        
        Args:
            user_id: 사용자 ID
            categories: 선택한 카테고리
            paper_ids: 선택한 논문 ID
            extracted_keywords: LLM에서 추출한 키워드
            
        Returns:
            임베딩 벡터 (리스트 형태)
        """
        try:
            # Preference Query 텍스트 생성
            categories_text = ", ".join(categories)
            keywords_text = ", ".join(extracted_keywords) if extracted_keywords else "papers"
            
            preference_query = f"""
            Categories of interest: {categories_text}
            Research topics and keywords: {keywords_text}
            """
            
            # 임베딩 생성
            embedding = embed_single(preference_query)
            embedding_list = embedding.tolist()
            
            # 프로필 업데이트
            profile_data = {
                "extracted_keywords": json.dumps(extracted_keywords),
                "preference_query": preference_query,
                "user_vector_json": json.dumps(embedding_list)
            }
            self.profile_repo.create_or_update(user_id, profile_data)
            
            return embedding_list
        
        except Exception as e:
            print(f"Error generating preference vector: {e}")
            return None
    
    def get_profile(self, user_id: str) -> Optional[dict]:
        """사용자 프로필 조회"""
        profile = self.profile_repo.get_by_user_id(user_id)
        
        if not profile:
            return None
        
        return {
            "user_id": profile.user_id,
            "categories": json.loads(profile.survey_categories or "[]"),
            "paper_ids": json.loads(profile.survey_paper_ids or "[]"),
            "keywords": json.loads(profile.extracted_keywords or "[]"),
            "preference_query": profile.preference_query,
            "has_vector": profile.user_vector_json is not None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }
