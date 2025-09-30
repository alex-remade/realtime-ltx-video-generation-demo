from dataclasses import dataclass
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class UserCommentParams(BaseModel):
    """Parameter overrides when using user comments"""
    guidance_scale: float = Field(default=5.0, description="Higher guidance to follow user comment closely")
    strength: float = Field(default=1.0, description="Lower strength for visual creativity")


@dataclass
class TwitchComment:
    username: str
    message: str
    timestamp: float
    user_id: Optional[str] = None
    badges: Optional[List[str]] = None
    emotes: Optional[Dict] = None
