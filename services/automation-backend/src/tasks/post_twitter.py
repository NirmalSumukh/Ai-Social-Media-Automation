import asyncio
from typing import Dict, Any, List
import logging

from ..http.twitter_client import TwitterClient

logger = logging.getLogger(__name__)

async def execute_twitter_post(
    content: str,
    access_token: str = None,
    access_token_secret: str = None,
    consumer_key: str = None,
    consumer_secret: str = None,
    hashtags: List[str] = None,
    media_url: str = None,
    user_credentials: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Execute Twitter posting task
    
    Args:
        content: Tweet content
        access_token: Twitter API access token
        access_token_secret: Twitter API access token secret
        consumer_key: Twitter API consumer key
        consumer_secret: Twitter API consumer secret
        hashtags: List of hashtags
        media_url: URL of media to attach
        user_credentials: Login credentials for fallback browser automation
    
    Returns:
        Dictionary with success status and details
    """
    
    client = TwitterClient()
    
    try:
        # Try HTTP API if we have all required OAuth credentials
        if all([access_token, access_token_secret, consumer_key, consumer_secret]):
            logger.info("Attempting Twitter post via HTTP API")
            
            result = await client.post_with_http(
                content=content,
                access_token=access_token,
                access_token_secret=access_token_secret,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                hashtags=hashtags,
                media_url=media_url
            )
            
            if result['success']:
                logger.info(f"Twitter HTTP API post successful: {result['post_id']}")
                return result
            
            logger.warning(f"Twitter HTTP API failed: {result['error']}")
        
        # If API fails or credentials not available, try browser automation
        if user_credentials and user_credentials.get('username') and user_credentials.get('password'):
            logger.info("Attempting Twitter post via browser automation")
            
            # Initialize browser and login
            await client.initialize_browser()
            login_success = await client.login_with_browser(
                username=user_credentials['username'],
                password=user_credentials['password']
            )
            
            if login_success:
                browser_result = await client.post_with_browser(
                    content=content,
                    hashtags=hashtags,
                    media_url=media_url
                )
                
                if browser_result['success']:
                    logger.info("Twitter browser automation post successful")
                    return browser_result
                else:
                    logger.error(f"Twitter browser automation failed: {browser_result['error']}")
            else:
                logger.error("Twitter browser login failed")
        
        # Return appropriate error message
        return {
            'success': False,
            'error': 'Twitter post failed: No valid authentication method available',
            'method': 'error'
        }
        
    except Exception as e:
        logger.error(f"Twitter post task failed with exception: {str(e)}")
        return {
            'success': False,
            'error': f"Twitter post failed: {str(e)}",
            'method': 'error'
        }
    
    finally:
        try:
            await client.cleanup()
        except Exception as e:
            logger.warning(f"Twitter client cleanup failed: {str(e)}")

def format_twitter_content(content: str, hashtags: List[str] = None) -> str:
    """
    Format content for Twitter, respecting character limits
    
    Args:
        content: Original content
        hashtags: List of hashtags to add
    
    Returns:
        Formatted content within Twitter's character limit
    """
    
    MAX_CHARS = 280
    
    # Add hashtags if provided
    if hashtags:
        hashtag_string = " " + " ".join([f"#{tag}" for tag in hashtags])
        available_chars = MAX_CHARS - len(hashtag_string)
        
        if len(content) > available_chars:
            # Truncate content to fit
            content = content[:available_chars-3] + "..."
        
        content += hashtag_string
    else:
        # No hashtags, just ensure content fits
        if len(content) > MAX_CHARS:
            content = content[:MAX_CHARS-3] + "..."
    
    return content