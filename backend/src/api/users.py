from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Dict
from sqlalchemy.orm import Session

from src.database.mysql import get_db
from src.repository.profile_repo import ProfileRepository

router = APIRouter(prefix="/users", tags=["users"])

class EnsureUserIn(BaseModel):
    user_id: str

class EnsureUserOut(BaseModel):
    user_id: str
    has_onboarded: bool

class OnboardingIn(BaseModel):
    user_id: str
    answers: Dict[str, Any]

class OnboardingOut(BaseModel):
    user_id: str
    has_onboarded: bool

@router.post("/ensure", response_model=EnsureUserOut)
def ensure_user(payload: EnsureUserIn, db: Session = Depends(get_db)):
    repo = ProfileRepository(db)
    p = repo.ensure_profile(payload.user_id)
    return EnsureUserOut(user_id=p.uuid, has_onboarded=bool(p.has_onboarded))

@router.post("/onboarding", response_model=OnboardingOut)
def save_onboarding(payload: OnboardingIn, db: Session = Depends(get_db)):
    repo = ProfileRepository(db)
    p = repo.set_onboarding(payload.user_id, payload.answers)
    return OnboardingOut(user_id=p.uuid, has_onboarded=bool(p.has_onboarded))
