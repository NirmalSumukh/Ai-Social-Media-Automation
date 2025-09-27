import requests
import json
from typing import Dict, Any, Optional, List
import tempfile
import os

class InstagramClient:
    """
    Instagram automation client using Meta's official Graph API
    This is the recommended approach for Instagram automation
    """
    
    def __init__(self):
        self.base_url = 'https://graph.facebook.com/v18.0'
    
    async def post_with_api(
        self,
        content: str,
        access_token: str,
        instagram_business_id: str,
        hashtags: List[str] = None,
        media_url: str = None
    ) -> Dict[str, Any]:
        """
        Post content using Instagram Graph API
        
        Args:
            content: Post caption
            access_token: Instagram Graph API access token
            instagram_business_id: Instagram Business Account ID
            hashtags: List of hashtags
            media_url: URL of image/video to post
        """
        try:
            # Prepare caption
            caption = content
            if hashtags:
                caption += "\\n\\n" + " ".join([f"#{tag}" for tag in hashtags])
            
            if media_url:
                # Post with media
                return await self._post_with_media(caption, access_token, instagram_business_id, media_url)
            else:
                # Text-only posts are not supported on Instagram
                # We'll create a simple graphic with the text instead
                return {
                    'success': False,
                    'error': 'Instagram requires media content. Text-only posts are not supported.',
                    'method': 'api'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'api'
            }
    
    async def _post_with_media(
        self,
        caption: str,
        access_token: str,
        instagram_business_id: str,
        media_url: str
    ) -> Dict[str, Any]:
        """Post with image or video media"""
        try:
            # Step 1: Create media object
            media_endpoint = f"{self.base_url}/{instagram_business_id}/media"
            
            # Determine if it's an image or video based on URL
            is_video = any(ext in media_url.lower() for ext in ['.mp4', '.mov', '.avi'])
            
            media_params = {
                'access_token': access_token,
                'caption': caption
            }
            
            if is_video:
                media_params['media_type'] = 'VIDEO'
                media_params['video_url'] = media_url
            else:
                media_params['image_url'] = media_url
            
            # Create media object
            response = requests.post(media_endpoint, data=media_params)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to create media object: {response.text}",
                    'method': 'api'
                }
            
            media_result = response.json()
            creation_id = media_result['id']
            
            # Step 2: Wait for media to be processed (for videos)
            if is_video:
                await self._wait_for_media_processing(creation_id, access_token)
            
            # Step 3: Publish the media
            publish_endpoint = f"{self.base_url}/{instagram_business_id}/media_publish"
            publish_params = {
                'creation_id': creation_id,
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_endpoint, data=publish_params)
            
            if publish_response.status_code == 200:
                result = publish_response.json()
                return {
                    'success': True,
                    'post_id': result['id'],
                    'method': 'api'
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to publish media: {publish_response.text}",
                    'method': 'api'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'method': 'api'
            }
    
    async def _wait_for_media_processing(self, creation_id: str, access_token: str, max_wait: int = 60):
        """Wait for video media to be processed"""
        import asyncio
        
        status_endpoint = f"{self.base_url}/{creation_id}"
        params = {
            'fields': 'status_code',
            'access_token': access_token
        }
        
        for _ in range(max_wait):
            response = requests.get(status_endpoint, params=params)
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status_code')
                
                if status == 'FINISHED':
                    return True
                elif status == 'ERROR':
                    raise Exception("Media processing failed")
            
            await asyncio.sleep(1)
        
        raise Exception("Media processing timeout")
    
    def create_text_image(self, text: str, width: int = 1080, height: int = 1080) -> str:
        """
        Create a simple image with text for Instagram posts
        This is a fallback for text-only content
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            import base64
            
            # Create image
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a nice font, fallback to default
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text
            draw.text((x, y), text, fill='black', font=font)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                img.save(tmp.name, 'PNG')
                return tmp.name
                
        except Exception as e:
            print(f"Failed to create text image: {e}")
            return None
    
    def get_instagram_business_id(self, access_token: str, facebook_page_id: str) -> Optional[str]:
        """Get Instagram Business Account ID from Facebook Page ID"""
        try:
            url = f"{self.base_url}/{facebook_page_id}"
            params = {
                'fields': 'instagram_business_account',
                'access_token': access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('instagram_business_account', {}).get('id')
                
        except Exception as e:
            print(f"Failed to get Instagram business ID: {e}")
        
        return None