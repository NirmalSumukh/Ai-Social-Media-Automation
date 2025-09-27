// apps/worker-scheduler/src/jobs/twitterJob.ts - Twitter Posting Job Handler
import axios from 'axios';

export interface TwitterJobData {
  postId: string;
  content: string;
  userId: string;
  accountId: string;
}

export async function processTwitterJob(data: TwitterJobData): Promise<void> {
  const { postId, content, userId, accountId } = data;
  
  try {
    console.log(`Processing Twitter post ${postId} for user ${userId}`);
    
    // Call the automation backend to post to Twitter
    const response = await axios.post(
      `${process.env.AUTOMATION_BACKEND_URL || 'http://automation-backend:8001'}/twitter/post`,
      {
        post_id: postId,
        content,
        user_id: userId,
        account_id: accountId,
      },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 60000, // 60 second timeout for social media posting
      }
    );

    if (response.status === 200) {
      console.log(`Twitter post ${postId} published successfully`);
      
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
      throw new Error(`Twitter API returned status ${response.status}`);
    }
  } catch (error: any) {
    console.error(`Failed to process Twitter job for post ${postId}:`, error.message);
    
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

export function validateTwitterContent(content: string): boolean {
  // Twitter character limit validation
  return content.length <= 280;
}

export function formatTwitterContent(content: string): string {
  // Ensure content fits Twitter's requirements
  if (content.length > 280) {
    return content.substring(0, 277) + '...';
  }
  return content;
}