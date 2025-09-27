import google.generativeai as genai
from typing import List, Optional, Dict, Any
import json
import re
from datetime import datetime

from app.models.post import BusinessContext, ContentSuggestion, PlatformType, PostType
from app.core.config import get_settings

class GeminiClient:
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def process_chat_message(
        self,
        message: str,
        business_context: Optional[BusinessContext] = None,
        platform: Optional[PlatformType] = None
    ) -> Dict[str, Any]:
        """Process a chat message and determine appropriate response"""
        
        # Determine if this is context building or content generation
        context_keywords = [
            'business', 'company', 'industry', 'audience', 'target', 'tone', 'voice',
            'about', 'we are', 'i am', 'my business', 'our company'
        ]
        
        content_keywords = [
            'create', 'generate', 'write', 'post', 'content', 'suggest', 'ideas',
            'help me with', 'make a post', 'social media'
        ]
        
        message_lower = message.lower()
        is_context_building = any(keyword in message_lower for keyword in context_keywords)
        is_content_request = any(keyword in message_lower for keyword in content_keywords)
        
        if is_context_building:
            return await self._handle_context_building(message, business_context)
        elif is_content_request and business_context:
            return await self._handle_content_request(message, business_context, platform)
        else:
            return await self._handle_general_conversation(message, business_context)
    
    async def _handle_context_building(
        self,
        message: str,
        existing_context: Optional[BusinessContext]
    ) -> Dict[str, Any]:
        """Extract business context from user message"""
        
        prompt = f"""
        Based on the user's message, extract business context information.
        If existing context is provided, update it with new information.
        
        User message: "{message}"
        
        Existing context: {existing_context.dict() if existing_context else "None"}
        
        Extract and return ONLY a JSON object with these fields (leave empty string if not mentioned):
        {{
            "business_type": "",
            "industry": "",
            "target_audience": "",
            "tone": "",
            "key_topics": [],
            "brand_voice": ""
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_match = re.search(r'\\{.*?\\}', response.text, re.DOTALL)
            if json_match:
                context_data = json.loads(json_match.group())
                
                # Merge with existing context
                if existing_context:
                    merged_context = existing_context.dict()
                    for key, value in context_data.items():
                        if value and value != "":
                            if key == "key_topics":
                                # Merge lists
                                existing_topics = merged_context.get(key, [])
                                new_topics = value if isinstance(value, list) else [value]
                                merged_context[key] = list(set(existing_topics + new_topics))
                            else:
                                merged_context[key] = value
                    context_data = merged_context
                
                friendly_response = self._generate_context_confirmation_response(context_data)
                
                return {
                    "response": friendly_response,
                    "updated_context": context_data,
                    "generate_content": False
                }
        except Exception as e:
            pass
        
        return {
            "response": "I'd love to learn more about your business! Can you tell me about your industry, target audience, or the type of content you'd like to create?",
            "generate_content": False
        }
    
    async def _handle_content_request(
        self,
        message: str,
        business_context: BusinessContext,
        platform: Optional[PlatformType]
    ) -> Dict[str, Any]:
        """Handle content generation requests"""
        
        suggestions = await self.generate_content_suggestions(
            business_context=business_context,
            platform=platform,
            specific_request=message
        )
        
        platform_text = f" for {platform}" if platform else ""
        response = f"I've generated some content ideas{platform_text} based on your business context. You can review and use any of these suggestions!"
        
        return {
            "response": response,
            "suggestions": suggestions,
            "generate_content": True
        }
    
    async def _handle_general_conversation(
        self,
        message: str,
        business_context: Optional[BusinessContext]
    ) -> Dict[str, Any]:
        """Handle general conversation"""
        
        context_text = ""
        if business_context:
            context_text = f"\\nUser's business context: {business_context.dict()}"
        
        prompt = f"""
        You are a helpful AI assistant for a social media management platform.
        Respond to the user's message in a friendly, helpful way.
        If they haven't set up their business context, encourage them to share information about their business.
        If they have context, offer to help create content.
        
        User message: "{message}"{context_text}
        
        Keep the response conversational and helpful, under 100 words.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {
                "response": response.text.strip(),
                "generate_content": False
            }
        except Exception as e:
            return {
                "response": "I'm here to help you create amazing social media content! Tell me about your business, or ask me to generate some posts for you.",
                "generate_content": False
            }
    
    def _generate_context_confirmation_response(self, context_data: Dict) -> str:
        """Generate a friendly confirmation response for context updates"""
        business_type = context_data.get('business_type', '')
        industry = context_data.get('industry', '')
        target_audience = context_data.get('target_audience', '')
        
        response = "Great! I've updated your business profile. "
        
        if business_type:
            response += f"I understand you're running a {business_type}"
            if industry:
                response += f" in the {industry} industry"
            response += ". "
        
        if target_audience:
            response += f"Your target audience is {target_audience}. "
        
        response += "Now I can create more personalized content for you! Just ask me to generate some posts, and I'll tailor them to your business."
        
        return response
    
    async def generate_content_suggestions(
        self,
        business_context: BusinessContext,
        platform: Optional[PlatformType] = None,
        content_type: Optional[PostType] = None,
        topic: Optional[str] = None,
        specific_request: Optional[str] = None
    ) -> List[ContentSuggestion]:
        """Generate content suggestions based on business context"""
        
        platforms = [platform] if platform else [PlatformType.TWITTER, PlatformType.LINKEDIN, PlatformType.INSTAGRAM]
        suggestions = []
        
        for plat in platforms:
            platform_prompt = self._build_platform_specific_prompt(
                platform=plat,
                business_context=business_context,
                content_type=content_type,
                topic=topic,
                specific_request=specific_request
            )
            
            try:
                response = self.model.generate_content(platform_prompt)
                parsed_suggestions = self._parse_content_suggestions(response.text, plat)
                suggestions.extend(parsed_suggestions)
            except Exception as e:
                # Fallback suggestion
                suggestions.append(self._create_fallback_suggestion(plat, business_context))
        
        return suggestions[:6]  # Limit to 6 suggestions
    
    def _build_platform_specific_prompt(
        self,
        platform: PlatformType,
        business_context: BusinessContext,
        content_type: Optional[PostType] = None,
        topic: Optional[str] = None,
        specific_request: Optional[str] = None
    ) -> str:
        """Build platform-specific content generation prompt"""
        
        platform_specs = {
            PlatformType.TWITTER: {
                "char_limit": 280,
                "style": "concise, engaging, hashtag-friendly",
                "features": "threads, polls, hashtags"
            },
            PlatformType.LINKEDIN: {
                "char_limit": 3000,
                "style": "professional, thought-leadership, industry insights",
                "features": "professional networking, longer form content"
            },
            PlatformType.INSTAGRAM: {
                "char_limit": 2200,
                "style": "visual-focused, storytelling, lifestyle",
                "features": "images, stories, reels, hashtags"
            }
        }
        
        spec = platform_specs[platform]
        
        prompt = f"""
        Create engaging social media content for {platform.value}.
        
        Business Context:
        - Business Type: {business_context.business_type}
        - Industry: {business_context.industry}
        - Target Audience: {business_context.target_audience}
        - Brand Tone: {business_context.tone}
        - Key Topics: {', '.join(business_context.key_topics)}
        - Brand Voice: {business_context.brand_voice or 'Professional and approachable'}
        
        Platform Requirements:
        - Character limit: {spec["char_limit"]}
        - Style: {spec["style"]}
        - Platform features: {spec["features"]}
        
        {f"Content Type: {content_type.value}" if content_type else ""}
        {f"Topic: {topic}" if topic else ""}
        {f"Specific Request: {specific_request}" if specific_request else ""}
        
        Generate 2 different post variations. For each post, provide:
        1. The main content text
        2. Relevant hashtags (3-5 for Twitter, 5-10 for Instagram/LinkedIn)
        3. Content type (text, image, or video)
        
        Format as JSON:
        [
            {{
                "content": "post content here",
                "hashtags": ["hashtag1", "hashtag2"],
                "post_type": "text"
            }}
        ]
        """
        
        return prompt
    
    def _parse_content_suggestions(self, response_text: str, platform: PlatformType) -> List[ContentSuggestion]:
        """Parse AI response into structured content suggestions"""
        suggestions = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\\[.*?\\]', response_text, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                
                for item in parsed_data:
                    suggestion = ContentSuggestion(
                        content=item.get('content', ''),
                        hashtags=item.get('hashtags', []),
                        post_type=PostType(item.get('post_type', 'text')),
                        platform=platform
                    )
                    suggestions.append(suggestion)
        except Exception as e:
            pass
        
        return suggestions
    
    def _create_fallback_suggestion(self, platform: PlatformType, context: BusinessContext) -> ContentSuggestion:
        """Create a fallback suggestion if AI generation fails"""
        fallback_content = f"Excited to share insights about {context.industry}! Our {context.business_type} is dedicated to serving {context.target_audience} with excellence."
        
        return ContentSuggestion(
            content=fallback_content,
            hashtags=[context.industry.lower().replace(' ', ''), context.business_type.lower().replace(' ', '')],
            post_type=PostType.TEXT,
            platform=platform
        )