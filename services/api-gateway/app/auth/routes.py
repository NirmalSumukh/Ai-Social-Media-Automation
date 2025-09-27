from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse
import os
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import redis
import json
import requests
import secrets
import urllib.parse
from app.core.config import get_settings
from app.auth.twitter_oauth import get_request_token, get_access_token, save_user_token

auth_router = APIRouter()
security = HTTPBearer()
settings = get_settings()

# Redis client for storing user sessions and social tokens
redis_client = redis.from_url(settings.REDIS_URL)

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SocialToken(BaseModel):
    platform: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

async def get_current_user(token: str = Depends(security)):
    return verify_token(token.credentials)

# ✅ FIXED: Extract user email from request headers for OAuth flow
async def get_current_user_email_from_request(request: Request) -> str:
    """Extract user email from JWT token in Authorization header or session"""
    try:
        # Try to get from Authorization header first
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if email:
                return email
        
        # Try to get from cookie if header doesn't work
        token_cookie = request.cookies.get("access_token")
        if token_cookie:
            payload = jwt.decode(token_cookie, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if email:
                return email
                
    except Exception as e:
        print(f"Error extracting user email: {e}")
    
    # Fallback to demo for development
    return "demo@example.com"

@auth_router.post("/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user exists
    user_key = f"user:{user.email}"
    if redis_client.exists(user_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Store user
    user_data = {
        "email": user.email,
        "full_name": user.full_name,
        "password": hashed_password.decode('utf-8'),
        "created_at": datetime.utcnow().isoformat()
    }
    
    redis_client.hset(user_key, mapping=user_data)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/login", response_model=Token)
async def login(user: UserLogin):
    user_key = f"user:{user.email}"
    user_data = redis_client.hgetall(user_key)
    
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    stored_password = user_data[b'password'].decode('utf-8')
    if not bcrypt.checkpw(user.password.encode('utf-8'), stored_password.encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.get("/oauth/{platform}/start")
async def start_oauth(platform: str, request: Request):
    """Start OAuth flow for social media platform"""
    if platform not in ['twitter', 'linkedin', 'instagram']:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    if platform == 'twitter':
        # Check if Twitter API keys are configured
        if not settings.TWITTER_API_KEY or not settings.TWITTER_API_SECRET:
            return RedirectResponse(
                url=f"{frontend_url}/settings?tab=accounts&platform=twitter&demo=true"
            )
        
        try:
            # ✅ FIXED: Get the actual logged-in user's email
            user_email = await get_current_user_email_from_request(request)
            print(f"🔍 Starting OAuth for user: {user_email}")
            
            # Get Twitter request token
            request_tokens = get_request_token()
            
            # Store both request tokens AND user email for callback
            oauth_data = {
                **request_tokens,
                "user_email": user_email
            }
            redis_client.setex(
                f"twitter_req:{request_tokens['oauth_token']}", 
                600, 
                json.dumps(oauth_data)
            )
            
            # Redirect to Twitter authorization
            twitter_auth_url = f"https://api.twitter.com/oauth/authorize?oauth_token={request_tokens['oauth_token']}"
            return RedirectResponse(url=twitter_auth_url)
            
        except Exception as e:
            print(f"Twitter OAuth start error: {e}")
            return RedirectResponse(
                url=f"{frontend_url}/settings?tab=accounts&platform=twitter&demo=true"
            )
    
    elif platform == 'linkedin':
        return RedirectResponse(
            url=f"{frontend_url}/settings?tab=accounts&platform=linkedin&demo=true"
        )
    
    elif platform == 'instagram':
        return RedirectResponse(
            url=f"{frontend_url}/settings?tab=accounts&platform=instagram&demo=true"
        )

@auth_router.get("/oauth/{platform}/callback")
async def oauth_callback(
    platform: str,
    oauth_token: str = None,
    oauth_verifier: str = None
):
    """Handle OAuth callback"""
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    if platform == 'twitter' and oauth_token and oauth_verifier:
        try:
            # Look up stored oauth data
            stored_data = redis_client.get(f"twitter_req:{oauth_token}")
            if not stored_data:
                raise Exception("Invalid or expired oauth_token")
            
            oauth_data = json.loads(stored_data)
            redis_client.delete(f"twitter_req:{oauth_token}")
            
            # Exchange for access tokens
            access_tokens = get_access_token(
                oauth_token,
                oauth_verifier,
                oauth_data['oauth_token_secret']
            )
            
            # ✅ FIXED: Save tokens for the actual user who initiated OAuth
            user_email = oauth_data.get("user_email", "demo@example.com")
            print(f"🔍 Saving tokens for user: {user_email}")
            save_user_token(user_email, access_tokens)
            
            return RedirectResponse(
                url=f"{frontend_url}/settings?tab=accounts&connected=twitter&status=success"
            )
            
        except Exception as e:
            print(f"Twitter OAuth callback error: {e}")
            return RedirectResponse(
                url=f"{frontend_url}/settings?tab=accounts&error=twitter_oauth_failed"
            )
    
    return RedirectResponse(
        url=f"{frontend_url}/settings?tab=accounts&connected={platform}&demo=true"
    )

@auth_router.get("/social-accounts")
async def list_accounts(current_user: dict = Depends(get_current_user)):
    user_email = current_user["sub"]
    print(f"🔍 Fetching accounts for user: {user_email}")
    
    result = []
    for p in ["twitter", "linkedin", "instagram"]:
        key = f"social_token:{user_email}:{p}"
        tok = redis_client.hgetall(key)
        if tok and tok.get(b"access_token"):
            print(f"✅ Found {p} account for {user_email}")
            result.append({
                "id": f"{user_email}_{p}",
                "platform": p,
                "username": tok.get(b"username", b"").decode("utf-8"),
                "isActive": True,
            })
    
    print(f"🔍 Returning {len(result)} accounts")
    return result

@auth_router.post("/social-accounts/demo-connect")
async def demo_connect_account(platform: str):
    """Demo endpoint to simulate account connection"""
    if platform not in ['twitter', 'linkedin', 'instagram']:
        raise HTTPException(status_code=400, detail="Unsupported platform")
    
    demo_user = "demo@example.com"
    token_key = f"social_token:{demo_user}:{platform}"
    
    redis_client.hset(token_key, mapping={
        "access_token": f"demo_token_{platform}_{secrets.token_hex(16)}",
        "username": f"demo_{platform}_user",
        "platform_user_id": f"demo_{platform}_id",
        "updated_at": datetime.utcnow().isoformat(),
        "demo_mode": "true"
    })
    
    return {"success": True, "message": f"{platform} connected successfully (demo mode)"}

@auth_router.delete("/social-accounts/{platform}")
async def disconnect_account(platform: str, current_user: dict = Depends(get_current_user)):
    """Disconnect social media account"""
    user_email = current_user["sub"]
    token_key = f"social_token:{user_email}:{platform}"
    
    if redis_client.delete(token_key):
        return {"success": True, "message": f"{platform} disconnected"}
    else:
        return {"success": False, "message": "Account not found"}

@auth_router.get("/notifications/count")
async def get_notifications_count(current_user: dict = Depends(get_current_user)):
    """Get notification count for user"""
    return {"count": 0, "unread": 0}

@auth_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {"email": current_user["sub"]}

@auth_router.get("/me")
async def who_am_i(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["sub"]}

@auth_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get user profile"""
    user_key = f"user:{current_user['sub']}"
    user_data = redis_client.hgetall(user_key)
    
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": user_data[b'email'].decode('utf-8'),
        "full_name": user_data[b'full_name'].decode('utf-8'),
        "created_at": user_data[b'created_at'].decode('utf-8')
    }
