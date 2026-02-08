from fastapi import APIRouter, Depends
from src.schemas.user import EnsureUserIn, EnsureUserOut, OnboardingIn, OnboardingOut
from sqlalchemy.orm import Session

from src.database.mysql import get_mysql_db
from src.repository.profile_repo import ProfileRepository
from src.repository.paper_repo import PaperRepository
from src.service.recsys.user_vector import build_user_vector_from_categories

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/ensure", response_model=EnsureUserOut)
def ensure_user(payload: EnsureUserIn, db: Session = Depends(get_mysql_db)):
    repo = ProfileRepository(db)
    p = repo.ensure_profile(payload.user_id)
    return EnsureUserOut(user_id=p.uuid, has_onboarded=bool(p.has_onboarded))

@router.post("/onboarding", response_model=OnboardingOut)
def save_onboarding(payload: OnboardingIn, db: Session = Depends(get_mysql_db)):
    repo = ProfileRepository(db)
    answers = payload.answers or {}
    categories = answers.get("categories")

    if isinstance(categories, list) and categories:
        paper_repo = PaperRepository(db)
        build_user_vector_from_categories(
            user_id=payload.user_id,
            categories=categories,
            profile_repo=repo,
            paper_repo=paper_repo,
        )

    p = repo.set_onboarding(payload.user_id, answers)
    return OnboardingOut(user_id=p.uuid, has_onboarded=bool(p.has_onboarded))
