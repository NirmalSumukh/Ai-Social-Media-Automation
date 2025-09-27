from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from typing import List, Optional
import redis
import json
import uuid
from datetime import datetime
from app.twitter_client import TwitterClient
from app.auth.routes import get_current_user
from app.models.post import Post, PostCreate, PostUpdate, PostStatus, PlatformType
from app.core.config import get_settings
from app.core.tasks import schedule_post_task

posts_router = APIRouter()
settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)

def generate_post_id():
    return str(uuid.uuid4())

def convert_empty_datetime(value: str) -> Optional[datetime]:
    """Convert empty string to None, otherwise parse as datetime"""
    if not value or value == "":
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except:
        return None

# STATS ENDPOINT MUST BE FIRST - BEFORE /{post_id}
@posts_router.get("/stats")
async def get_posts_stats(current_user: dict = Depends(get_current_user)):
    """Get posts statistics"""
    user_email = current_user['sub']
    user_posts_key = f"user_posts:{user_email}"
    post_ids = redis_client.lrange(user_posts_key, 0, -1)

    total_posts = 0
    published_posts = 0
    draft_posts = 0
    scheduled_posts = 0
    failed_posts = 0

    for post_id in post_ids:
        post_key = f"post:{post_id.decode('utf-8')}"
        post_data = redis_client.hgetall(post_key)
        if post_data:
            total_posts += 1
            status = post_data.get(b'status', b'').decode('utf-8')
            if status == PostStatus.PUBLISHED:
                published_posts += 1
            elif status == PostStatus.DRAFT:
                draft_posts += 1
            elif status == PostStatus.SCHEDULED:
                scheduled_posts += 1
            elif status == PostStatus.FAILED:
                failed_posts += 1

    return {
        "total_posts": total_posts,
        "published_posts": published_posts,
        "draft_posts": draft_posts,
        "scheduled_posts": scheduled_posts,
        "failed_posts": failed_posts
    }

@posts_router.post("/", response_model=Post)
async def create_post(
    post: PostCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Create a new post"""
    user_email = current_user['sub']
    post_id = generate_post_id()
    now = datetime.utcnow()

    post_data = {
        "id": post_id,
        "user_id": user_email,
        "title": post.title or "",
        "content": post.content,
        "platform": post.platform,
        "post_type": post.post_type,
        "media_url": post.media_url or "",
        "hashtags": json.dumps(post.hashtags or []),
        "scheduled_at": post.scheduled_at.isoformat() if post.scheduled_at else "",
        "status": PostStatus.DRAFT if not post.scheduled_at else PostStatus.SCHEDULED,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "published_at": "",
        "error_message": ""
    }

    # Store post
    post_key = f"post:{post_id}"
    redis_client.hset(post_key, mapping=post_data)

    # Add to user's posts list
    user_posts_key = f"user_posts:{user_email}"
    redis_client.lpush(user_posts_key, post_id)

    # Schedule the post if scheduled_at is provided
    if post.scheduled_at:
        background_tasks.add_task(schedule_post_task, post_id, post.scheduled_at)

    # Convert data for Post model response
    response_data = post_data.copy()
    response_data['hashtags'] = json.loads(response_data['hashtags'])
    response_data['scheduled_at'] = convert_empty_datetime(response_data['scheduled_at'])
    response_data['published_at'] = convert_empty_datetime(response_data['published_at'])

    return Post(**response_data)

@posts_router.get("/", response_model=List[Post])
async def get_posts(
    platform: Optional[PlatformType] = None,
    status: Optional[PostStatus] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get all posts for the user"""
    try:
        user_email = current_user['sub']
        user_posts_key = f"user_posts:{user_email}"
        post_ids = redis_client.lrange(user_posts_key, 0, limit-1)

        posts = []
        for post_id in post_ids:
            try:
                post_key = f"post:{post_id.decode('utf-8')}"
                post_data = redis_client.hgetall(post_key)
                if post_data:
                    # Convert bytes to strings
                    post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}
                    post_dict['hashtags'] = json.loads(post_dict.get('hashtags', '[]'))
                    
                    # Fix datetime conversion
                    post_dict['scheduled_at'] = convert_empty_datetime(post_dict.get('scheduled_at', ''))
                    post_dict['published_at'] = convert_empty_datetime(post_dict.get('published_at', ''))
                    
                    # Apply filters
                    if platform and post_dict['platform'] != platform:
                        continue
                    if status and post_dict['status'] != status:
                        continue

                    posts.append(Post(**post_dict))
            except Exception as e:
                print(f"Error processing post {post_id}: {e}")
                continue

        return posts
    except Exception as e:
        print(f"Error in get_posts: {e}")
        return []

# THIS ROUTE MUST BE AFTER /stats
@posts_router.get("/{post_id}", response_model=Post)
async def get_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific post"""
    user_email = current_user['sub']
    post_key = f"post:{post_id}"
    post_data = redis_client.hgetall(post_key)

    if not post_data:
        raise HTTPException(status_code=404, detail="Post not found")

    post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}

    # Check if user owns the post
    if post_dict['user_id'] != user_email:
        raise HTTPException(status_code=403, detail="Not authorized to access this post")

    post_dict['hashtags'] = json.loads(post_dict.get('hashtags', '[]'))
    post_dict['scheduled_at'] = convert_empty_datetime(post_dict.get('scheduled_at', ''))
    post_dict['published_at'] = convert_empty_datetime(post_dict.get('published_at', ''))

    return Post(**post_dict)

@posts_router.put("/{post_id}", response_model=Post)
async def update_post(
    post_id: str,
    post_update: PostUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a post"""
    user_email = current_user['sub']
    post_key = f"post:{post_id}"
    post_data = redis_client.hgetall(post_key)

    if not post_data:
        raise HTTPException(status_code=404, detail="Post not found")

    post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}

    if post_dict['user_id'] != user_email:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")

    # Update fields
    update_data = post_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == 'hashtags' and value:
            post_dict[key] = json.dumps(value)
        elif key == 'scheduled_at' and value:
            post_dict[key] = value.isoformat()
            if post_dict['status'] == PostStatus.DRAFT:
                post_dict['status'] = PostStatus.SCHEDULED
        elif value is not None:
            post_dict[key] = str(value)

    post_dict['updated_at'] = datetime.utcnow().isoformat()
    redis_client.hset(post_key, mapping=post_dict)

    # Convert for response
    response_data = post_dict.copy()
    response_data['hashtags'] = json.loads(response_data.get('hashtags', '[]'))
    response_data['scheduled_at'] = convert_empty_datetime(response_data.get('scheduled_at', ''))
    response_data['published_at'] = convert_empty_datetime(response_data.get('published_at', ''))

    return Post(**response_data)

@posts_router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a post"""
    user_email = current_user['sub']
    post_key = f"post:{post_id}"
    post_data = redis_client.hgetall(post_key)

    if not post_data:
        raise HTTPException(status_code=404, detail="Post not found")

    post_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in post_data.items()}

    if post_dict['user_id'] != user_email:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    user_posts_key = f"user_posts:{user_email}"
    redis_client.lrem(user_posts_key, 0, post_id)
    redis_client.delete(post_key)

    return {"message": "Post deleted successfully"}

@posts_router.post("/{post_id}/publish")
async def publish_post(
    post_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Publish a post immediately"""
    user_email = current_user['sub']
    post_key = f"post:{post_id}"

    post_data = redis_client.hgetall(post_key)
    if not post_data:
        raise HTTPException(status_code=404, detail="Post not found")

    if post_data.get(b'user_id', b'').decode('utf-8') != user_email:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        platform = post_data.get(b'platform', b'').decode('utf-8')
        content = post_data.get(b'content', b'').decode('utf-8')
        hashtags_str = post_data.get(b'hashtags', b'[]').decode('utf-8')
        hashtags = json.loads(hashtags_str) if hashtags_str else []

        if platform == 'twitter':
            from app.twitter_client import TwitterClient
            
            twitter_client = TwitterClient(user_email)
            result = twitter_client.post_tweet(content, hashtags)

            if result.get('success'):
                now = datetime.utcnow()
                redis_client.hset(post_key, mapping={
                    "status": "published",
                    "published_at": now.isoformat(),
                    "updated_at": now.isoformat(),
                    "external_id": result.get('tweet_id', '')
                })

                return {
                    "success": True,
                    "message": f"Post published to {platform} successfully!",
                    "post_id": post_id,
                    "external_id": result.get('tweet_id'),
                    "published_at": now.isoformat()
                }
            else:
                redis_client.hset(post_key, mapping={
                    "status": "failed",
                    "error_message": result.get('error', 'Unknown error'),
                    "updated_at": datetime.utcnow().isoformat()
                })
                raise HTTPException(status_code=500, detail=result.get('error', 'Publishing failed'))

        else:
            now = datetime.utcnow()
            redis_client.hset(post_key, mapping={
                "status": "published",
                "published_at": now.isoformat(),
                "updated_at": now.isoformat()
            })

            return {
                "success": True,
                "message": f"Post published to {platform} successfully (demo mode)!",
                "post_id": post_id,
                "published_at": now.isoformat()
            }

    except Exception as e:
        redis_client.hset(post_key, mapping={
            "status": "failed",
            "error_message": str(e),
            "updated_at": datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=500, detail=f"Failed to publish post: {str(e)}")

@posts_router.post("/upload-media")
async def upload_media(
    media: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload media file for posts"""
    return {
        "url": f"https://placeholder-media.com/{media.filename}",
        "type": "image" if media.content_type.startswith("image/") else "video",
        "filename": media.filename
    }
