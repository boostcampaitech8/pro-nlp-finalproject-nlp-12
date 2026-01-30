"""
Repository 패턴 사용 예제

이 파일은 Repository 패턴을 사용하는 방법을 보여줍니다.
"""
from sqlalchemy.orm import Session
from src.repository.paper_repository import PaperRepository
from src.repository.user_profile_repository import UserProfileRepository
from src.repository.user_event_repository import UserEventRepository
from src.entity.paper import Paper
from src.entity.user_event import UserEvent
import json


def example_paper_repository(db: Session):
    """PaperRepository 사용 예제"""
    paper_repo = PaperRepository(db)
    
    # 1. ArXiv ID로 논문 조회
    paper = paper_repo.get_by_arxiv_id("2301.00001")
    if paper:
        print(f"Found paper: {paper.title}")
    
    # 2. 여러 ID로 논문 조회
    papers = paper_repo.get_by_ids([1, 2, 3, 4, 5])
    print(f"Found {len(papers)} papers")
    
    # 3. 최신 논문 조회
    recent_papers = paper_repo.get_recent_papers(limit=10)
    print(f"Recent papers: {len(recent_papers)}")
    
    # 4. 카테고리별 논문 조회
    cs_papers = paper_repo.get_by_categories(["cs.AI", "cs.LG"], limit=20)
    print(f"CS papers: {len(cs_papers)}")
    
    # 5. 인용수가 높은 논문 조회
    popular_papers = paper_repo.get_by_categories_with_citations(
        categories=["cs.AI"],
        min_citations=10,
        limit=20
    )
    print(f"Popular CS.AI papers: {len(popular_papers)}")
    
    # 6. 논문 존재 여부 확인
    exists = paper_repo.exists_by_arxiv_id("2301.00001")
    print(f"Paper exists: {exists}")
    
    # 7. 전체 논문 수
    total = paper_repo.count_all()
    print(f"Total papers in DB: {total}")


def example_user_profile_repository(db: Session):
    """UserProfileRepository 사용 예제"""
    profile_repo = UserProfileRepository(db)
    
    user_id = "test_user_123"
    
    # 1. 프로필 조회
    profile = profile_repo.get_by_user_id(user_id)
    if profile:
        print(f"Found profile for {user_id}")
    
    # 2. 프로필 생성 또는 업데이트
    profile_data = {
        "survey_categories": json.dumps(["cs.AI", "cs.LG"]),
        "extracted_keywords": json.dumps(["machine learning", "neural networks"]),
        "user_vector_json": json.dumps([0.1, 0.2, 0.3])
    }
    profile = profile_repo.create_or_update(user_id, profile_data)
    print(f"Profile updated for {user_id}")
    
    # 3. 프로필 존재 여부 확인
    exists = profile_repo.exists_by_user_id(user_id)
    print(f"Profile exists: {exists}")


def example_user_event_repository(db: Session):
    """UserEventRepository 사용 예제"""
    event_repo = UserEventRepository(db)
    
    user_id = "test_user_123"
    
    # 1. 이벤트 생성
    event = UserEventsMvp(
        user_id=user_id,
        paper_id=1,
        event_type="like",
        weight=1.0
    )
    created_event = event_repo.create(event)
    print(f"Event created: {created_event.event_id}")
    
    # 2. 사용자의 모든 이벤트 조회
    events = event_repo.get_by_user_id(user_id, limit=100)
    print(f"User has {len(events)} events")
    
    # 3. 특정 타입의 이벤트만 조회
    likes = event_repo.get_by_user_id(user_id, event_type="like", limit=50)
    print(f"User has {len(likes)} likes")
    
    # 4. 최근 7일간의 이벤트
    recent_events = event_repo.get_recent_events(user_id, days=7)
    print(f"Recent events (7 days): {len(recent_events)}")
    
    # 5. 상호작용한 논문 ID 목록
    liked_paper_ids = event_repo.get_interacted_paper_ids(
        user_id,
        event_types=["like", "bookmark"]
    )
    print(f"User liked/bookmarked {len(liked_paper_ids)} papers")
    
    # 6. 이벤트 수 카운트
    total_events = event_repo.count_by_user(user_id)
    total_likes = event_repo.count_by_user(user_id, event_type="like")
    print(f"Total events: {total_events}, Total likes: {total_likes}")
    
    # 7. 특정 이벤트 존재 여부
    has_liked = event_repo.exists_event(user_id, paper_id=1, event_type="like")
    print(f"User liked paper 1: {has_liked}")


def example_service_with_repositories(db: Session):
    """Service에서 Repository 사용 예제"""
    paper_repo = PaperRepository(db)
    profile_repo = UserProfileRepository(db)
    event_repo = UserEventRepository(db)
    
    user_id = "test_user_123"
    
    # 1. 사용자 프로필 가져오기
    profile = profile_repo.get_by_user_id(user_id)
    if not profile:
        print("User has no profile")
        return
    
    # 2. 사용자가 이미 본 논문 제외
    seen_paper_ids = event_repo.get_interacted_paper_ids(
        user_id, 
        event_types=["dislike"]
    )
    
    # 3. 최신 논문 가져오기
    all_papers = paper_repo.get_recent_papers(limit=100)
    
    # 4. 필터링
    recommended_papers = [
        p for p in all_papers 
        if p.id not in seen_paper_ids
    ]
    
    print(f"Recommending {len(recommended_papers)} papers to {user_id}")
    
    return recommended_papers[:30]  # Top 30


def example_bulk_operations(db: Session):
    """Bulk 작업 예제"""
    event_repo = UserEventRepository(db)
    
    # 여러 이벤트 한번에 생성
    # 새 UserEvent 엔티티는 weight 필드가 없고, user_id는 integer FK
    events = [
        UserEvent(user_id=1, paper_id=i, event_type="impression")  # weight 제거, user_id를 정수로
        for i in range(1, 11)
    ]
    
    created_events = event_repo.bulk_create(events)
    print(f"Created {len(created_events)} events at once")


if __name__ == "__main__":
    print("이 파일은 예제 코드입니다. 실제로 실행하려면 DB 세션이 필요합니다.")
    print("\n사용 방법:")
    print("from sqlalchemy.orm import Session")
    print("from src.database.mysql import get_db")
    print("")
    print("db = next(get_db())")
    print("example_paper_repository(db)")
