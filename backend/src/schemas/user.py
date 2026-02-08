from pydantic import BaseModel
from typing import Dict, Any

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