import asyncio
import json
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import requests
import time
import random
import base64
import hmac
import hashlib
from urllib.parse import quote, urlencode

from ..http.http_sniffer import SocialMediaHTTPClient

class TwitterClient:
    """Twitter automation client using both HTTP requests and browser automation"""
    
    def __init__(self):
        self.http_client = SocialMediaHTTPClient('twitter')
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
    
    async def login_with_browser(self, username: str, password: str) -> bool:
        """Login using browser automation"""
        try:
            if not self.page:
                await self.initialize_browser()
            
            # Navigate to Twitter login
            await self.page.goto('https://twitter.com/i/flow/login')
            await self.page.wait_for_selector('input[autocomplete="username"]')
            
            # Fill username
            await self.page.fill('input[autocomplete="username"]', username)
            await self.page.click('div[role="button"]:has-text("Next")')
            
            # Wait for password field
            await self.page.wait_for_selector('input[name="password"]')
            await self.page.fill('input[name="password"]', password)
            
            # Submit login
            await self.page.click('div[data-testid="LoginForm_Login_Button"]')
            
            # Wait for successful login
            await self.page.wait_for_url('https://twitter.com/home', timeout=15000)
            
            return True
            
        except Exception as e:
            print(f"Browser login failed: {e}")
            return False
    
    async def post_with_http(
        self,
        content: str,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        consumer_secret: str,
        hashtags: List[str] = None,
        media_url: str = None
    ) -> Dict[str, Any]:
        """
        Post using HTTP requests with OAuth 1.0a
        This uses Twitter's API v2
        """
        try:
            # Prepare content
            full_content = content
            if hashtags:
                full_content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            # Twitter API v2 endpoint
            url = 'https://api.twitter.com/2/tweets'
            
            tweet_data = {
                "text": full_content[:280]  # Twitter character limit
            }
            
            # Handle media if provided
            if media_url:
                # First upload media
                media_id = await self._upload_media(media_url, access_token, access_token_secret, consumer_key, consumer_secret)
                if media_id:
                    tweet_data["media"] = {"media_ids": [media_id]}
            
            # Generate OAuth headers
            oauth_headers = self._generate_oauth_headers(
                'POST', url, tweet_data, consumer_key, consumer_secret, access_token, access_token_secret
            )
            
            response = requests.post(
                url,
                json=tweet_data,
                headers={
                    'Authorization': oauth_headers,
                    'Content-Type': 'application/json'
                }
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    'success': True,
                    'post_id': result['data']['id'],
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
        """Post using browser automation"""
        try:
            if not self.page:
                return {'success': False, 'error': 'Browser not initialized'}
            
            # Navigate to Twitter home
            await self.page.goto('https://twitter.com/home')
            await self.page.wait_for_selector('div[data-testid="tweetTextarea_0"]')
            
            # Prepare full content
            full_content = content
            if hashtags:
                full_content += " " + " ".join([f"#{tag}" for tag in hashtags])
            
            # Click in tweet compose area
            await self.page.click('div[data-testid="tweetTextarea_0"]')
            
            # Type content
            await self.page.fill('div[data-testid="tweetTextarea_0"]', full_content)
            
            # Handle media upload if provided
            if media_url:
                try:
                    # Download image temporarily and upload
                    # This is a simplified version - in production you'd handle this more robustly
                    file_input = await self.page.locator('input[data-testid="fileInput"]')
                    if file_input:
                        # This would require downloading the file locally first
                        pass
                except Exception:
                    pass
            
            # Random delay before tweeting
            await asyncio.sleep(random.uniform(1, 3))
            
            # Click tweet button
            await self.page.click('div[data-testid="tweetButtonInline"]')
            
            # Wait for tweet to be posted
            await asyncio.sleep(2)
            
            return {
                'success': True,
                'post_id': 'browser_tweet',
                'method': 'browser'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'browser'
            }
    
    def _generate_oauth_headers(
        self,
        method: str,
        url: str,
        data: dict,
        consumer_key: str,
        consumer_secret: str,
        access_token: str,
        access_token_secret: str
    ) -> str:
        """Generate OAuth 1.0a authorization header"""
        import time
        import random
        import string
        
        # OAuth parameters
        oauth_params = {
            'oauth_consumer_key': consumer_key,
            'oauth_nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': str(int(time.time())),
            'oauth_token': access_token,
            'oauth_version': '1.0'
        }
        
        # Create signature base string
        params = oauth_params.copy()
        if method == 'GET' and data:
            params.update(data)
        
        param_string = '&'.join([f"{quote(str(k))}={quote(str(v))}" for k, v in sorted(params.items())])
        base_string = f"{method}&{quote(url)}&{quote(param_string)}"
        
        # Create signing key
        signing_key = f"{quote(consumer_secret)}&{quote(access_token_secret)}"
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        oauth_params['oauth_signature'] = signature
        
        # Create authorization header
        auth_header = 'OAuth ' + ', '.join([f'{quote(str(k))}="{quote(str(v))}"' for k, v in sorted(oauth_params.items())])
        
        return auth_header
    
    async def _upload_media(
        self,
        media_url: str,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        consumer_secret: str
    ) -> Optional[str]:
        """Upload media to Twitter"""
        try:
            # Download media
            response = requests.get(media_url)
            if response.status_code != 200:
                return None
            
            media_data = response.content
            
            # Upload to Twitter
            upload_url = 'https://upload.twitter.com/1.1/media/upload.json'
            
            files = {'media': media_data}
            oauth_headers = self._generate_oauth_headers(
                'POST', upload_url, {}, consumer_key, consumer_secret, access_token, access_token_secret
            )
            
            upload_response = requests.post(
                upload_url,
                files=files,
                headers={'Authorization': oauth_headers}
            )
            
            if upload_response.status_code == 200:
                result = upload_response.json()
                return result.get('media_id_string')
                
        except Exception as e:
            print(f"Media upload failed: {e}")
        
        return None
    
    async def cleanup(self):
        """Cleanup browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()