// apps/worker-scheduler/src/jobs/linkedinJob.ts - LinkedIn Posting Job Handler
import axios from 'axios';

export interface LinkedInJobData {
  postId: string;
  content: string;
  userId: string;
  accountId: string;
  imageUrl?: string;
}

export async function processLinkedInJob(data: LinkedInJobData): Promise<void> {
  const { postId, content, userId, accountId, imageUrl } = data;
  
  try {
    console.log(`Processing LinkedIn post ${postId} for user ${userId}`);
    
    // Call the automation backend to post to LinkedIn
    const response = await axios.post(
      `${process.env.AUTOMATION_BACKEND_URL || 'http://automation-backend:8001'}/linkedin/post`,
      {
        post_id: postId,
        content,
        user_id: userId,
        account_id: accountId,
        image_url: imageUrl,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 60000, // 60 second timeout for social media posting
      }
    );

    if (response.status === 200) {
      console.log(`LinkedIn post ${postId} published successfully`);
      
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
      throw new Error(`LinkedIn API returned status ${response.status}`);
    }
  } catch (error: any) {
    console.error(`Failed to process LinkedIn job for post ${postId}:`, error.message);
    
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

export function validateLinkedInContent(content: string): boolean {
  // LinkedIn character limit validation (3000 chars for posts)
  return content.length <= 3000;
}

export function formatLinkedInContent(content: string): string {
  // Ensure content fits LinkedIn's requirements
  if (content.length > 3000) {
    return content.substring(0, 2997) + '...';
  }
  return content;
}

export function addLinkedInHashtags(content: string, hashtags: string[] = []): string {
  if (hashtags.length === 0) return content;
  
  const hashtagString = hashtags
    .filter(tag => tag.length > 0)
    .map(tag => tag.startsWith('#') ? tag : `#${tag}`)
    .join(' ');
  
  return `${content}\n\n${hashtagString}`;
}