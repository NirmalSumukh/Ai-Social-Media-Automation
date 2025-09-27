from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import redis
import json

from src.http.linkedin_client import LinkedInClient
from src.http.twitter_client import TwitterClient
from src.http.instagram_client import InstagramClient

app = FastAPI(
    title="Social Media Automation Backend",
    description="Backend service for automating social media posts",
    version="1.0.0"
)

# Redis client for getting user tokens
redis_client = redis.from_url("redis://redis:6379")

class PublishRequest(BaseModel):
    post_id: str
    user_id: str
    platform: str
    content: str
    hashtags: List[str] = []
    media_url: Optional[str] = None
    post_type: str = "text"

class PublishResponse(BaseModel):
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None
    method: Optional[str] = None

# Initialize clients
linkedin_client = LinkedInClient()
twitter_client = TwitterClient()
instagram_client = InstagramClient()

@app.get("/")
async def root():
    return {"message": "Social Media Automation Backend", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "automation-backend"}

@app.post("/publish", response_model=PublishResponse)
async def publish_post(request: PublishRequest):
    """Main endpoint to publish a post to a social media platform"""
    
    try:
        # Get user's social tokens
        token_key = f"social_token:{request.user_id}:{request.platform}"
        token_data = redis_client.hgetall(token_key)
        
        if not token_data:
            return PublishResponse(
                success=False,
                error=f"No authentication token found for {request.platform}"
            )
        
        # Convert bytes to strings
        token_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in token_data.items()}
        access_token = token_dict.get('access_token', '')
        
        if not access_token:
            return PublishResponse(
                success=False,
                error=f"Invalid authentication token for {request.platform}"
            )
        
        # Route to appropriate platform client
        if request.platform == 'linkedin':
            result = await publish_to_linkedin(request, access_token)
        elif request.platform == 'twitter':
            result = await publish_to_twitter(request, token_dict)
        elif request.platform == 'instagram':
            result = await publish_to_instagram(request, access_token)
        else:
            return PublishResponse(
                success=False,
                error=f"Unsupported platform: {request.platform}"
            )
        
        return PublishResponse(**result)
        
    except Exception as e:
        return PublishResponse(
            success=False,
            error=f"Unexpected error: {str(e)}"
        )

async def publish_to_linkedin(request: PublishRequest, access_token: str) -> Dict[str, Any]:
    """Publish to LinkedIn using API or browser automation"""
    
    try:
        # Try HTTP API first
        result = await linkedin_client.post_with_http(
            content=request.content,
            access_token=access_token,
            hashtags=request.hashtags,
            media_url=request.media_url
        )
        
        if result['success']:
            return result
        
        # If API fails, try browser automation as fallback
        # Note: This would require stored login credentials
        browser_result = await linkedin_client.post_with_browser(
            content=request.content,
            hashtags=request.hashtags,
            media_url=request.media_url
        )
        
        return browser_result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'method': 'linkedin'
        }
    finally:
        await linkedin_client.cleanup()

async def publish_to_twitter(request: PublishRequest, token_dict: Dict[str, str]) -> Dict[str, Any]:
    """Publish to Twitter using API or browser automation"""
    
    try:
        # Get Twitter API credentials from environment or token storage
        # For demo purposes, we'll use browser automation
        # In production, you'd use proper OAuth tokens
        
        access_token = token_dict.get('access_token', '')
        access_token_secret = token_dict.get('access_token_secret', '')
        consumer_key = token_dict.get('consumer_key', '')
        consumer_secret = token_dict.get('consumer_secret', '')
        
        if access_token and access_token_secret and consumer_key and consumer_secret:
            # Try API first
            result = await twitter_client.post_with_http(
                content=request.content,
                access_token=access_token,
                access_token_secret=access_token_secret,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                hashtags=request.hashtags,
                media_url=request.media_url
            )
            
            if result['success']:
                return result
        
        # Fallback to browser automation
        browser_result = await twitter_client.post_with_browser(
            content=request.content,
            hashtags=request.hashtags,
            media_url=request.media_url
        )
        
        return browser_result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'method': 'twitter'
        }
    finally:
        await twitter_client.cleanup()

async def publish_to_instagram(request: PublishRequest, access_token: str) -> Dict[str, Any]:
    """Publish to Instagram using Meta Graph API"""
    
    try:
        # Get Instagram Business Account ID
        instagram_business_id = redis_client.get(f"instagram_business_id:{request.user_id}")
        
        if instagram_business_id:
            instagram_business_id = instagram_business_id.decode('utf-8')
        else:
            return {
                'success': False,
                'error': 'Instagram Business Account ID not found',
                'method': 'instagram'
            }
        
        result = await instagram_client.post_with_api(
            content=request.content,
            access_token=access_token,
            instagram_business_id=instagram_business_id,
            hashtags=request.hashtags,
            media_url=request.media_url
        )
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'method': 'instagram'
        }

@app.post("/test-connection/{platform}")
async def test_platform_connection(platform: str, user_id: str):
    """Test connection to a social media platform"""
    
    token_key = f"social_token:{user_id}:{platform}"
    token_data = redis_client.hgetall(token_key)
    
    if not token_data:
        raise HTTPException(status_code=404, detail=f"No token found for {platform}")
    
    # Basic token validation
    token_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in token_data.items()}
    access_token = token_dict.get('access_token', '')
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Invalid access token")
    
    return {
        "platform": platform,
        "user_id": user_id,
        "connection_status": "valid",
        "token_exists": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)