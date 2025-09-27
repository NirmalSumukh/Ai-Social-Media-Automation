import asyncio
import redis
import json
import httpx
from datetime import datetime
from celery import Celery
from typing import Optional

from app.core.config import get_settings
from app.models.post import PostStatus

settings = get_settings()

# Initialize Celery
celery_app = Celery(
    'social_media_tasks',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Redis client
redis_client = redis.from_url(settings.REDIS_URL)

@celery_app.task
def schedule_post_task(post_id: str, scheduled_time: datetime):
    """Task to schedule a post for publishing"""
    try:
        # Calculate delay until scheduled time
        now = datetime.utcnow()
        delay = (scheduled_time - now).total_seconds()
        
        if delay <= 0:
            # Publish immediately
            publish_post_task.apply_async(args=[post_id])
        else:
            # Schedule for later
            publish_post_task.apply_async(args=[post_id], countdown=delay)
        
        return f"Post {post_id} scheduled successfully"
    except Exception as e:
        return f"Error scheduling post {post_id}: {str(e)}"

@celery_app.task
def publish_post_task(post_id: str):
    """Task to publish a post to social media platforms"""
    try:
        # Get post data
        post_key = f"post:{post_id}"
        post_data = redis_client.hgetall(post_key)
        
        if not post_data:
            return f"Post {post_id} not found"
        
        post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}
        
        # Update status to publishing
        post_dict['status'] = 'publishing'
        redis_client.hset(post_key, mapping=post_dict)
        
        # Get user's social tokens
        user_email = post_dict['user_id']
        platform = post_dict['platform']
        
        # Call automation service
        automation_url = f"{settings.AUTOMATION_SERVICE_URL}/publish"
        payload = {
            "post_id": post_id,
            "user_id": user_email,
            "platform": platform,
            "content": post_dict['content'],
            "hashtags": json.loads(post_dict.get('hashtags', '[]')),
            "media_url": post_dict.get('media_url', ''),
            "post_type": post_dict['post_type']
        }
        
        with httpx.Client() as client:
            response = client.post(automation_url, json=payload, timeout=30.0)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    # Update post status to published
                    post_dict['status'] = PostStatus.PUBLISHED
                    post_dict['published_at'] = datetime.utcnow().isoformat()
                    post_dict['error_message'] = ''
                else:
                    # Update post status to failed
                    post_dict['status'] = PostStatus.FAILED
                    post_dict['error_message'] = result.get('error', 'Unknown error')
            else:
                # Update post status to failed
                post_dict['status'] = PostStatus.FAILED
                post_dict['error_message'] = f"HTTP {response.status_code}: {response.text}"
        
        # Save updated post
        redis_client.hset(post_key, mapping=post_dict)
        
        return f"Post {post_id} published successfully"
        
    except Exception as e:
        # Update post status to failed
        post_dict['status'] = PostStatus.FAILED
        post_dict['error_message'] = str(e)
        redis_client.hset(post_key, mapping=post_dict)
        
        return f"Error publishing post {post_id}: {str(e)}"

@celery_app.task
def retry_failed_posts():
    """Task to retry failed posts"""
    # This would scan for failed posts and retry them
    # Implementation depends on specific retry logic
    pass