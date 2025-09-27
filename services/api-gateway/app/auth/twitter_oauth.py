import base64, hmac, hashlib, secrets, time, urllib.parse, requests, json
from datetime import datetime
from app.core.config import get_settings
import redis

settings = get_settings()
redis_client = redis.from_url(settings.REDIS_URL)

REQUEST_URL  = "https://api.twitter.com/oauth/request_token"
AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
ACCESS_URL   = "https://api.twitter.com/oauth/access_token"
CALLBACK_URL = settings.TWITTER_CALLBACK_URL

def _percent(v:str) -> str:
    return urllib.parse.quote(v, safe="")

def _signature(method:str, url:str, params:dict, consumer_secret:str, token_secret:str="") -> str:
    sbase = "&".join([f"{_percent(k)}={_percent(str(params[k]))}" for k in sorted(params)])
    bstring = f"{method.upper()}&{_percent(url)}&{_percent(sbase)}"
    skey   = f"{_percent(consumer_secret)}&{_percent(token_secret)}"
    return base64.b64encode(hmac.new(skey.encode(), bstring.encode(), hashlib.sha1).digest()).decode()

def get_request_token():
    p = {
        "oauth_callback": CALLBACK_URL,
        "oauth_consumer_key": settings.TWITTER_API_KEY,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    p["oauth_signature"] = _signature("POST", REQUEST_URL, p, settings.TWITTER_API_SECRET)
    hdr = "OAuth " + ", ".join([f'{k}="{_percent(p[k])}"' for k in p])
    r = requests.post(REQUEST_URL, headers={"Authorization": hdr})
    r.raise_for_status()
    return dict(urllib.parse.parse_qsl(r.text))

def get_access_token(oauth_token, oauth_verifier, token_secret):
    p = {
        "oauth_consumer_key": settings.TWITTER_API_KEY,
        "oauth_token": oauth_token,
        "oauth_verifier": oauth_verifier,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0",
    }
    p["oauth_signature"] = _signature("POST", ACCESS_URL, p,
                                      settings.TWITTER_API_SECRET, token_secret)
    hdr = "OAuth " + ", ".join([f'{k}="{_percent(p[k])}"' for k in p])
    r = requests.post(ACCESS_URL, headers={"Authorization": hdr})
    r.raise_for_status()
    return dict(urllib.parse.parse_qsl(r.text))

def save_user_token(email:str, tokens:dict):
    key = f"social_token:{email}:twitter"
    redis_client.hset(key, mapping={
        "access_token":        tokens["oauth_token"],
        "access_token_secret": tokens["oauth_token_secret"],
        "username":            tokens["screen_name"],
        "user_id":             tokens["user_id"],
        "updated_at":          datetime.utcnow().isoformat()
    })
