from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import redis
import json
from datetime import datetime

from app.auth.routes import get_current_user
from app.utils.gemini import GeminiClient
from app.models.post import BusinessContext, ContentSuggestion, PlatformType, PostType
from app.core.config import get_settings

chatbot_router = APIRouter()
settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)
gemini_client = GeminiClient()

class ChatMessage(BaseModel):
    message: str
    platform: Optional[PlatformType] = None

class ChatResponse(BaseModel):
    response: str
    suggestions: Optional[List[ContentSuggestion]] = None
    context_updated: bool = False

class BusinessContextUpdate(BaseModel):
    business_type: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    key_topics: Optional[List[str]] = None
    brand_voice: Optional[str] = None

@chatbot_router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    chat_message: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """Main chat endpoint for interacting with the AI chatbot"""
    user_email = current_user['sub']
    context_key = f"business_context:{user_email}"
    
    # Get existing business context
    context_data = redis_client.get(context_key)
    business_context = None
    if context_data:
        context_data = json.loads(context_data)
        business_context = BusinessContext(**context_data)
    
    # Process the message and determine if it's context building or content generation
    response_data = await gemini_client.process_chat_message(
        message=chat_message.message,
        business_context=business_context,
        platform=chat_message.platform
    )
    
    # Update context if new information was provided
    context_updated = False
    if response_data.get('updated_context'):
        updated_context = response_data['updated_context']
        redis_client.set(context_key, json.dumps(updated_context))
        context_updated = True
    
    # Generate content suggestions if requested
    suggestions = []
    if response_data.get('generate_content') and business_context:
        suggestions = await gemini_client.generate_content_suggestions(
            business_context=business_context,
            platform=chat_message.platform,
            specific_request=chat_message.message
        )
    
    return ChatResponse(
        response=response_data['response'],
        suggestions=suggestions,
        context_updated=context_updated
    )

@chatbot_router.get("/context", response_model=BusinessContext)
async def get_business_context(current_user: dict = Depends(get_current_user)):
    """Get the current business context for the user"""
    user_email = current_user['sub']
    context_key = f"business_context:{user_email}"
    
    context_data = redis_client.get(context_key)
    if not context_data:
        raise HTTPException(status_code=404, detail="Business context not found")
    
    return BusinessContext(**json.loads(context_data))

@chatbot_router.put("/context", response_model=BusinessContext)
async def update_business_context(
    context_update: BusinessContextUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update business context manually"""
    user_email = current_user['sub']
    context_key = f"business_context:{user_email}"
    
    # Get existing context
    context_data = redis_client.get(context_key)
    if context_data:
        current_context = json.loads(context_data)
    else:
        current_context = {}
    
    # Update with new data
    update_data = context_update.dict(exclude_unset=True)
    current_context.update(update_data)
    
    # Store updated context
    redis_client.set(context_key, json.dumps(current_context))
    
    return BusinessContext(**current_context)

@chatbot_router.post("/generate-content", response_model=List[ContentSuggestion])
async def generate_content(
    platform: Optional[PlatformType] = None,
    content_type: Optional[PostType] = None,
    topic: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate content suggestions based on business context"""
    user_email = current_user['sub']
    context_key = f"business_context:{user_email}"
    
    context_data = redis_client.get(context_key)
    if not context_data:
        raise HTTPException(
            status_code=400, 
            detail="Please set up your business context first by chatting with the bot"
        )
    
    business_context = BusinessContext(**json.loads(context_data))
    
    suggestions = await gemini_client.generate_content_suggestions(
        business_context=business_context,
        platform=platform,
        content_type=content_type,
        topic=topic
    )
    
    return suggestions

@chatbot_router.get("/conversation-history")
async def get_conversation_history(current_user: dict = Depends(get_current_user)):
    """Get the chat history for the user"""
    user_email = current_user['sub']
    history_key = f"chat_history:{user_email}"
    
    history_data = redis_client.lrange(history_key, 0, -1)
    history = []
    
    for item in history_data:
        history.append(json.loads(item))
    
    return {"history": history}