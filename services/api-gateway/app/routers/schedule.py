from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime, timedelta
import redis
import json
from calendar import monthrange
from pydantic import BaseModel

from app.auth.routes import get_current_user
from app.models.post import Post, PlatformType, PostStatus
from app.core.config import get_settings

schedule_router = APIRouter()
settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)

class CalendarEvent(BaseModel):
    date: str
    posts: List[Post]
    post_count: int

@schedule_router.get("/calendar")
async def get_calendar_view(
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user)
):
    """Get calendar view of scheduled posts for a specific month"""
    user_email = current_user['sub']
    user_posts_key = f"user_posts:{user_email}"
    
    # Get the date range for the month
    start_date = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    # Get all post IDs for the user
    post_ids = redis_client.lrange(user_posts_key, 0, -1)
    
    # Group posts by date
    calendar_data = {}
    
    for post_id in post_ids:
        post_key = f"post:{post_id.decode('utf-8')}"
        post_data = redis_client.hgetall(post_key)
        
        if not post_data:
            continue
            
        post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}
        
        # Only include scheduled or published posts with dates in range
        if not post_dict.get('scheduled_at'):
            continue
            
        try:
            scheduled_at = datetime.fromisoformat(post_dict['scheduled_at'])
        except:
            continue
            
        if not (start_date <= scheduled_at <= end_date):
            continue
        
        # Group by date
        date_key = scheduled_at.strftime('%Y-%m-%d')
        if date_key not in calendar_data:
            calendar_data[date_key] = []
        
        post_dict['hashtags'] = json.loads(post_dict.get('hashtags', '[]'))
        calendar_data[date_key].append(Post(**post_dict))
    
    # Convert to calendar events format
    calendar_events = []
    for date_str, posts in calendar_data.items():
        calendar_events.append({
            "date": date_str,
            "posts": posts,
            "post_count": len(posts)
        })
    
    return {
        "year": year,
        "month": month,
        "events": calendar_events
    }

@schedule_router.get("/upcoming")
async def get_upcoming_posts(
    days: int = 7,
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming posts for the next N days"""
    user_email = current_user['sub']
    user_posts_key = f"user_posts:{user_email}"
    
    now = datetime.utcnow()
    future_date = now + timedelta(days=days)
    
    post_ids = redis_client.lrange(user_posts_key, 0, -1)
    upcoming_posts = []
    
    for post_id in post_ids:
        post_key = f"post:{post_id.decode('utf-8')}"
        post_data = redis_client.hgetall(post_key)
        
        if not post_data:
            continue
            
        post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}
        
        if post_dict.get('status') != PostStatus.SCHEDULED:
            continue
            
        if not post_dict.get('scheduled_at'):
            continue
            
        try:
            scheduled_at = datetime.fromisoformat(post_dict['scheduled_at'])
        except:
            continue
            
        if now <= scheduled_at <= future_date:
            post_dict['hashtags'] = json.loads(post_dict.get('hashtags', '[]'))
            upcoming_posts.append(Post(**post_dict))
    
    # Sort by scheduled time
    upcoming_posts.sort(key=lambda x: x.scheduled_at)
    
    return {"posts": upcoming_posts}

@schedule_router.get("/stats")
async def get_schedule_stats(current_user: dict = Depends(get_current_user)):
    """Get scheduling statistics"""
    user_email = current_user['sub']
    user_posts_key = f"user_posts:{user_email}"
    
    post_ids = redis_client.lrange(user_posts_key, 0, -1)
    
    stats = {
        "total_posts": 0,
        "draft_posts": 0,
        "scheduled_posts": 0,
        "published_posts": 0,
        "failed_posts": 0,
        "posts_by_platform": {
            "twitter": 0,
            "linkedin": 0,
            "instagram": 0
        }
    }
    
    for post_id in post_ids:
        post_key = f"post:{post_id.decode('utf-8')}"
        post_data = redis_client.hgetall(post_key)
        
        if not post_data:
            continue
            
        post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}
        
        stats["total_posts"] += 1
        
        status = post_dict.get('status', '')
        if status == PostStatus.DRAFT:
            stats["draft_posts"] += 1
        elif status == PostStatus.SCHEDULED:
            stats["scheduled_posts"] += 1
        elif status == PostStatus.PUBLISHED:
            stats["published_posts"] += 1
        elif status == PostStatus.FAILED:
            stats["failed_posts"] += 1
        
        platform = post_dict.get('platform', '')
        if platform in stats["posts_by_platform"]:
            stats["posts_by_platform"][platform] += 1
    
    return stats