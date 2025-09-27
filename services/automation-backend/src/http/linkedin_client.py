import asyncio
import json
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import requests
import time
import random

from ..http.http_sniffer import SocialMediaHTTPClient

class LinkedInClient:
    """LinkedIn automation client using both HTTP requests and browser automation"""
    
    def __init__(self):
        self.http_client = SocialMediaHTTPClient('linkedin')
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
    
    async def login_with_browser(self, email: str, password: str) -> bool:
        """Login using browser automation as fallback"""
        try:
            if not self.page:
                await self.initialize_browser()
            
            # Navigate to LinkedIn login
            await self.page.goto('https://www.linkedin.com/login')
            await self.page.wait_for_selector('#username')
            
            # Fill credentials
            await self.page.fill('#username', email)
            await self.page.fill('#password', password)
            
            # Submit form
            await self.page.click('button[type="submit"]')
            
            # Wait for redirect
            await self.page.wait_for_url('https://www.linkedin.com/feed/', timeout=10000)
            
            return True
            
        except Exception as e:
            print(f"Browser login failed: {e}")
            return False
    
    async def post_with_http(
        self,
        content: str,
        access_token: str,
        hashtags: List[str] = None,
        media_url: str = None
    ) -> Dict[str, Any]:
        """
        Post using HTTP requests (requires valid access token)
        This method uses LinkedIn's official API when possible
        """
        try:
            # LinkedIn API endpoint for sharing
            url = 'https://api.linkedin.com/v2/ugcPosts'
            
            # Prepare content
            full_content = content
            if hashtags:
                full_content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            # Prepare post data
            post_data = {
                "author": f"urn:li:person:{self._get_person_id(access_token)}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": full_content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Add media if provided
            if media_url:
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                    {
                        "status": "READY",
                        "description": {
                            "text": "Shared content"
                        },
                        "media": media_url,
                        "title": {
                            "text": "Shared Image"
                        }
                    }
                ]
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            response = requests.post(url, json=post_data, headers=headers)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'post_id': response.json().get('id'),
                    'method': 'api'
                }
            else:
                return {
                    'success': False,
                    'error': f"API error: {response.status_code} - {response.text}",
                    'method': 'api'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'api'
            }
    
    async def post_with_browser(
        self,
        content: str,
        hashtags: List[str] = None,
        media_url: str = None
    ) -> Dict[str, Any]:
        """Post using browser automation as fallback"""
        try:
            if not self.page:
                return {'success': False, 'error': 'Browser not initialized'}
            
            # Navigate to LinkedIn feed
            await self.page.goto('https://www.linkedin.com/feed/')
            await self.page.wait_for_selector('div[data-test-id="share-box-trigger"]')
            
            # Click on share box
            await self.page.click('div[data-test-id="share-box-trigger"]')
            await self.page.wait_for_selector('div[data-test-id="share-creation-state-know-to"]')
            
            # Wait for editor to be ready
            await self.page.wait_for_selector('div[role="textbox"][data-placeholder]')
            
            # Prepare full content
            full_content = content
            if hashtags:
                full_content += "\\n\\n" + " ".join([f"#{tag}" for tag in hashtags])
            
            # Type content
            await self.page.fill('div[role="textbox"][data-placeholder]', full_content)
            
            # Handle media upload if provided
            if media_url:
                # This would require downloading the image and uploading it
                # For now, we'll skip media upload in browser mode
                pass
            
            # Random delay before posting
            await asyncio.sleep(random.uniform(2, 4))
            
            # Click post button
            await self.page.click('button[data-test-id="share-creation-state-share-button"]')
            
            # Wait for success indication
            await self.page.wait_for_selector('div[data-test-id="success-message"]', timeout=10000)
            
            return {
                'success': True,
                'post_id': 'browser_post',
                'method': 'browser'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'browser'
            }
    
    def _get_person_id(self, access_token: str) -> str:
        """Get LinkedIn person ID from access token"""
        try:
            url = 'https://api.linkedin.com/v2/people/~'
            headers = {
                'Authorization': f'Bearer {access_token}',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('id', '')
        except Exception:
            pass
        
        return ''
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()