# services/api-gateway/app/main.py - Fixed version
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from dotenv import load_dotenv
from app.auth.routes import auth_router, get_current_user # Import get_current_user here
from app.auth import routes as auth_routes
from app.routers.chatbot import chatbot_router
from app.routers.posts import posts_router
from app.routers.schedule import schedule_router
from app.core.config import get_settings

load_dotenv()
settings = get_settings()

app = FastAPI(
    title="AI Social Media Platform API",
    description="API for AI-powered social media automation platform",
    version="1.0.0"
)

# --- CORRECT CORS Configuration ---
# This configuration is correct. If errors persist, it points to an issue
# in the router code itself, not the CORS middleware.
origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# --- DEBUGGING ENDPOINT ---
# This is a new endpoint to test if CORS is working correctly for authenticated routes.
@app.get("/test-cors")
async def test_cors_endpoint(current_user: dict = Depends(get_current_user)):
    """A simple test endpoint to verify CORS and authentication."""
    return {"message": "CORS test successful!", "user": current_user}


# Include routers
app.include_router(auth_routes.auth_router, prefix="")
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(chatbot_router, prefix="/chatbot", tags=["AI Chatbot"])
app.include_router(posts_router, prefix="/posts", tags=["Posts"])
app.include_router(schedule_router, prefix="/schedule", tags=["Scheduling"])

@app.get("/")
async def root():
    return {"message": "AI Social Media Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "api-gateway"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False # Changed to False for stability
    )

