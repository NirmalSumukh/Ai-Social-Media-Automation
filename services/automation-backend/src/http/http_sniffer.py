import requests
import json
import time
import random
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode

class HTTPSniffer:
    """
    Helper class to replay HTTP requests captured from HTTP Toolkit
    for social media automation
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def add_random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def update_headers(self, headers: Dict[str, str]):
        """Update session headers"""
        self.session.headers.update(headers)
    
    def replay_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ) -> requests.Response:
        """
        Replay a captured HTTP request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            headers: Request headers
            data: Form data or raw body
            json_data: JSON payload
            params: URL parameters
            cookies: Request cookies
            timeout: Request timeout
        """
        
        # Merge headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
        
        # Add cookies if provided
        if cookies:
            self.session.cookies.update(cookies)
        
        # Add random delay
        self.add_random_delay()
        
        # Make the request
        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=request_headers,
            data=data,
            json=json_data,
            params=params,
            timeout=timeout
        )
        
        return response
    
    def extract_csrf_token(self, response: requests.Response, token_name: str = 'csrfToken') -> Optional[str]:
        """Extract CSRF token from response"""
        try:
            # Try to find token in response text
            import re
            pattern = f'"{token_name}"\\s*:\\s*"([^"]+)"'
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
            
            # Try alternative patterns
            pattern = f'name="{token_name}"\\s+value="([^"]+)"'
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
                
        except Exception:
            pass
        
        return None
    
    def extract_json_value(self, response: requests.Response, key: str) -> Optional[Any]:
        """Extract a value from JSON response"""
        try:
            data = response.json()
            return data.get(key)
        except Exception:
            return None

class SocialMediaHTTPClient(HTTPSniffer):
    """Extended HTTP client for social media platform automation"""
    
    def __init__(self, platform: str):
        super().__init__()
        self.platform = platform.lower()
        self.setup_platform_defaults()
    
    def setup_platform_defaults(self):
        """Setup platform-specific default headers and settings"""
        if self.platform == 'twitter':
            self.default_headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'X-Twitter-Active-User': 'yes',
                'X-Twitter-Client-Language': 'en'
            })
        elif self.platform == 'linkedin':
            self.default_headers.update({
                'X-Requested-With': 'XMLHttpRequest',
                'X-Li-Lang': 'en_US',
                'X-Li-Track': json.dumps({'clientVersion': '1.0.0'})
            })
    
    def login_flow(self, username: str, password: str) -> bool:
        """
        Perform login flow for the platform
        This should be customized based on captured requests from HTTP Toolkit
        """
        # This is a template - actual implementation would depend on 
        # the specific requests captured for each platform
        pass
    
    def post_content(
        self,
        content: str,
        media_urls: List[str] = None,
        hashtags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Post content to the platform
        This should be customized based on captured requests from HTTP Toolkit
        """
        # This is a template - actual implementation would depend on 
        # the specific requests captured for each platform
        pass