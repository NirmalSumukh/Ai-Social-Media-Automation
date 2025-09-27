import requests
import base64
import hashlib
import hmac
import time
import secrets
import urllib.parse
from app.core.config import get_settings
import redis

settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)

def _percent_encode(string):
    return urllib.parse.quote(str(string), safe='')

def _generate_signature(method, url, params, consumer_secret, token_secret=""):
    """Generate OAuth 1.0a signature"""
    param_string = "&".join([f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted(params.items())])
    base_string = f"{method.upper()}&{_percent_encode(url)}&{_percent_encode(param_string)}"
    signing_key = f"{_percent_encode(consumer_secret)}&{_percent_encode(token_secret)}"
    signature = base64.b64encode(hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()).decode()
    return signature

class TwitterClient:
    def __init__(self, user_email: str):
        # Get user's Twitter tokens from Redis
        token_key = f"social_token:{user_email}:twitter"
        token_data = redis_client.hgetall(token_key)
        
        if not token_data or not token_data.get(b'access_token'):
            raise Exception("Twitter account not connected")
        
        self.consumer_key = settings.TWITTER_API_KEY
        self.consumer_secret = settings.TWITTER_API_SECRET
        self.access_token = token_data[b'access_token'].decode()
        self.access_token_secret = token_data[b'access_token_secret'].decode()
        
    def post_tweet(self, content: str, hashtags: list = None) -> dict:
        """Post a tweet using Twitter API v2"""
        
        # Prepare content
        full_content = content
        if hashtags:
            full_content += " " + " ".join([f"#{tag.strip('#')}" for tag in hashtags])
        
        # Truncate to Twitter's limit
        full_content = full_content[:280]
        
        # Twitter API v2 endpoint
        url = "https://api.twitter.com/2/tweets"
        
        # OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.access_token,
            "oauth_version": "1.0"
        }
        
        # Generate signature
        signature = _generate_signature("POST", url, oauth_params, self.consumer_secret, self.access_token_secret)
        oauth_params["oauth_signature"] = signature
        
        # Create authorization header
        auth_header = "OAuth " + ", ".join([f'{k}="{_percent_encode(v)}"' for k, v in oauth_params.items()])
        
        # Make request
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
        
        payload = {"text": full_content}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                return {
                    "success": True,
                    "tweet_id": result["data"]["id"],
                    "text": result["data"]["text"]
                }
            else:
                return {
                    "success": False,
                    "error": f"Twitter API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
