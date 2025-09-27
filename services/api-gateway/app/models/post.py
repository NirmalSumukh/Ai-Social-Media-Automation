from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class PlatformType(str, Enum):
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"

class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

class PostBase(BaseModel):
    title: Optional[str] = None
    content: str
    platform: PlatformType
    post_type: PostType = PostType.TEXT
    media_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    hashtags: Optional[List[str]] = []

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    hashtags: Optional[List[str]] = None

class Post(PostBase):
    id: str
    user_id: str
    status: PostStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class ContentSuggestion(BaseModel):
    content: str
    hashtags: List[str]
    post_type: PostType
    platform: PlatformType

class BusinessContext(BaseModel):
    business_type: str
    industry: str
    target_audience: str
    tone: str
    key_topics: List[str]
    brand_voice: Optional[str] = None