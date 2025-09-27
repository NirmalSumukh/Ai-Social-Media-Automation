// apps/worker-scheduler/src/jobs/instagramJob.ts - Instagram Posting Job Handler
import axios from 'axios';

export interface InstagramJobData {
  postId: string;
  content: string;
  userId: string;
  accountId: string;
  imageUrl: string; // Instagram requires an image
  isStory?: boolean;
}

export async function processInstagramJob(data: InstagramJobData): Promise<void> {
  const { postId, content, userId, accountId, imageUrl, isStory = false } = data;
  
  try {
    console.log(`Processing Instagram ${isStory ? 'story' : 'post'} ${postId} for user ${userId}`);
    
    // Call the automation backend to post to Instagram
    const response = await axios.post(
      `${process.env.AUTOMATION_BACKEND_URL || 'http://automation-backend:8001'}/instagram/post`,
      {
        post_id: postId,
        content,
        user_id: userId,
        account_id: accountId,
        image_url: imageUrl,
        is_story: isStory,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 90000, // 90 second timeout for image upload
      }
    );

    if (response.status === 200) {
      console.log(`Instagram ${isStory ? 'story' : 'post'} ${postId} published successfully`);
      
      // Update post status in the database via API Gateway
      await axios.patch(
        `${process.env.API_GATEWAY_URL || 'http://api-gateway:8000'}/posts/${postId}`,
        {
          status: 'published',
          published_at: new Date().toISOString(),
          platform_response: response.data,
        }
      );
    } else {
      throw new Error(`Instagram API returned status ${response.status}`);
    }
  } catch (error: any) {
    console.error(`Failed to process Instagram job for post ${postId}:`, error.message);
    
    // Update post status to failed
    await axios.patch(
      `${process.env.API_GATEWAY_URL || 'http://api-gateway:8000'}/posts/${postId}`,
      {
        status: 'failed',
        error_message: error.message,
      }
    ).catch(console.error);
    
    throw error;
  }
}

export function validateInstagramContent(content: string): boolean {
  // Instagram caption limit (2200 characters)
  return content.length <= 2200;
}

export function formatInstagramContent(content: string): string {
  // Ensure content fits Instagram's requirements
  if (content.length > 2200) {
    return content.substring(0, 2197) + '...';
  }
  return content;
}

export function addInstagramHashtags(content: string, hashtags: string[] = []): string {
  if (hashtags.length === 0) return content;
  
  // Instagram allows up to 30 hashtags
  const limitedHashtags = hashtags.slice(0, 30);
  
  const hashtagString = limitedHashtags
    .filter(tag => tag.length > 0)
    .map(tag => tag.startsWith('#') ? tag : `#${tag}`)
    .join(' ');
  
  return `${content}\n\n${hashtagString}`;
}

export function validateInstagramImage(imageUrl: string): boolean {
  if (!imageUrl) return false;
  
  // Check if URL is valid image format
  const validExtensions = ['.jpg', '.jpeg', '.png', '.gif'];
  const url = imageUrl.toLowerCase();
  
  return validExtensions.some(ext => url.includes(ext)) || url.includes('base64');
}