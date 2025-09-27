import asyncio
from typing import Dict, Any, List
import logging

from ..http.linkedin_client import LinkedInClient

logger = logging.getLogger(__name__)

async def execute_linkedin_post(
    content: str,
    access_token: str,
    hashtags: List[str] = None,
    media_url: str = None,
    user_credentials: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Execute LinkedIn posting task
    
    Args:
        content: Post content
        access_token: LinkedIn API access token
        hashtags: List of hashtags
        media_url: URL of media to attach
        user_credentials: Login credentials for fallback browser automation
    
    Returns:
        Dictionary with success status and details
    """
    
    client = LinkedInClient()
    
    try:
        logger.info("Attempting LinkedIn post via HTTP API")
        
        # Try HTTP API first
        result = await client.post_with_http(
            content=content,
            access_token=access_token,
            hashtags=hashtags,
            media_url=media_url
        )
        
        if result['success']:
            logger.info(f"LinkedIn HTTP API post successful: {result['post_id']}")
            return result
        
        logger.warning(f"LinkedIn HTTP API failed: {result['error']}")
        
        # If API fails and we have credentials, try browser automation
        if user_credentials and user_credentials.get('email') and user_credentials.get('password'):
            logger.info("Attempting LinkedIn post via browser automation")
            
            # Initialize browser and login
            await client.initialize_browser()
            login_success = await client.login_with_browser(
                email=user_credentials['email'],
                password=user_credentials['password']
            )
            
            if login_success:
                browser_result = await client.post_with_browser(
                    content=content,
                    hashtags=hashtags,
                    media_url=media_url
                )
                
                if browser_result['success']:
                    logger.info("LinkedIn browser automation post successful")
                    return browser_result
                else:
                    logger.error(f"LinkedIn browser automation failed: {browser_result['error']}")
            else:
                logger.error("LinkedIn browser login failed")
        
        # Return the original API error if browser automation isn't available or fails
        return result
        
    except Exception as e:
        logger.error(f"LinkedIn post task failed with exception: {str(e)}")
        return {
            'success': False,
            'error': f"LinkedIn post failed: {str(e)}",
            'method': 'error'
        }
    
    finally:
        try:
            await client.cleanup()
        except Exception as e:
            logger.warning(f"LinkedIn client cleanup failed: {str(e)}")