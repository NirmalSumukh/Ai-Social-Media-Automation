// apps/worker-scheduler/src/index.ts - Main Worker Scheduler Entry Point (Redis Fixed)
import { Worker, Queue } from 'bullmq';
import IORedis from 'ioredis';
import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

// Create Redis connection with proper configuration
const redis = new IORedis(process.env.REDIS_URL || 'redis://redis:6379', {
  maxRetriesPerRequest: 3,
  lazyConnect: true,
  connectTimeout: 10000,
  commandTimeout: 5000,
});

const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://api-gateway:8000';

// Create queue instances for adding jobs
const postQueue = new Queue('post-queue', { connection: redis });

// Post processing worker
const postWorker = new Worker(
  'post-queue',
  async (job) => {
    const { postId, action } = job.data;
    
    try {
      switch (action) {
        case 'publish':
          await publishPost(postId);
          break;
        case 'schedule':
          await schedulePost(postId);
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }
    } catch (error: any) {
      console.error(`Failed to process post ${postId}:`, error.message);
      throw error;
    }
  },
  {
    connection: redis,
    concurrency: 5,
    removeOnComplete: { count: 100 },
    removeOnFail: { count: 50 },
  }
);

async function publishPost(postId: string): Promise<void> {
  try {
    console.log(`Publishing post ${postId}`);
    
    const response = await axios.post(
      `${API_GATEWAY_URL}/automation/publish`,
      { post_id: postId },
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000,
      }
    );
    
    console.log(`Post ${postId} published successfully`);
  } catch (error: any) {
    console.error(`Failed to publish post ${postId}:`, error.message);
    throw error;
  }
}

async function schedulePost(postId: string): Promise<void> {
  try {
    console.log(`Scheduling post ${postId}`);
    
    // Get post details from API
    const postResponse = await axios.get(`${API_GATEWAY_URL}/posts/${postId}`);
    const post = postResponse.data;
    
    // Schedule the post for future publication
    const scheduledTime = new Date(post.scheduled_for);
    const now = new Date();
    
    if (scheduledTime <= now) {
      // If scheduled time has passed, publish immediately
      await publishPost(postId);
    } else {
      // Schedule for future publication
      const delayMs = scheduledTime.getTime() - now.getTime();
      
      await postQueue.add(
        'publish-scheduled-post',
        { postId, action: 'publish' },
        {
          delay: delayMs,
          removeOnComplete: { count: 10 },
          removeOnFail: { count: 5 },
        }
      );
      
      console.log(`Post ${postId} scheduled for ${scheduledTime.toISOString()}`);
    }
  } catch (error: any) {
    console.error(`Failed to schedule post ${postId}:`, error.message);
    throw error;
  }
}

// Platform-specific workers
const twitterWorker = new Worker(
  'twitter-queue',
  async (job) => {
    const { postId, content, userId, accountId } = job.data;
    
    try {
      console.log(`Processing Twitter post ${postId} for user ${userId}`);
      
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
          timeout: 60000,
        }
      );

      if (response.status === 200) {
        console.log(`Twitter post ${postId} published successfully`);
        
        // Update post status
        await axios.patch(
          `${API_GATEWAY_URL}/posts/${postId}`,
          {
            status: 'published',
            published_at: new Date().toISOString(),
            platform_response: response.data,
          }
        );
      }
    } catch (error: any) {
      console.error(`Failed to process Twitter job for post ${postId}:`, error.message);
      
      // Update post status to failed
      await axios.patch(
        `${API_GATEWAY_URL}/posts/${postId}`,
        {
          status: 'failed',
          error_message: error.message,
        }
      ).catch(console.error);
      
      throw error;
    }
  },
  {
    connection: redis,
    concurrency: 3,
    removeOnComplete: { count: 50 },
    removeOnFail: { count: 25 },
  }
);

const linkedinWorker = new Worker(
  'linkedin-queue',
  async (job) => {
    const { postId, content, userId, accountId, imageUrl } = job.data;
    
    try {
      console.log(`Processing LinkedIn post ${postId} for user ${userId}`);
      
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
          timeout: 60000,
        }
      );

      if (response.status === 200) {
        console.log(`LinkedIn post ${postId} published successfully`);
        
        await axios.patch(
          `${API_GATEWAY_URL}/posts/${postId}`,
          {
            status: 'published',
            published_at: new Date().toISOString(),
            platform_response: response.data,
          }
        );
      }
    } catch (error: any) {
      console.error(`Failed to process LinkedIn job for post ${postId}:`, error.message);
      
      await axios.patch(
        `${API_GATEWAY_URL}/posts/${postId}`,
        {
          status: 'failed',
          error_message: error.message,
        }
      ).catch(console.error);
      
      throw error;
    }
  },
  {
    connection: redis,
    concurrency: 3,
    removeOnComplete: { count: 50 },
    removeOnFail: { count: 25 },
  }
);

const instagramWorker = new Worker(
  'instagram-queue',
  async (job) => {
    const { postId, content, userId, accountId, imageUrl } = job.data;
    
    try {
      console.log(`Processing Instagram post ${postId} for user ${userId}`);
      
      const response = await axios.post(
        `${process.env.AUTOMATION_BACKEND_URL || 'http://automation-backend:8001'}/instagram/post`,
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
          timeout: 90000,
        }
      );

      if (response.status === 200) {
        console.log(`Instagram post ${postId} published successfully`);
        
        await axios.patch(
          `${API_GATEWAY_URL}/posts/${postId}`,
          {
            status: 'published',
            published_at: new Date().toISOString(),
            platform_response: response.data,
          }
        );
      }
    } catch (error: any) {
      console.error(`Failed to process Instagram job for post ${postId}:`, error.message);
      
      await axios.patch(
        `${API_GATEWAY_URL}/posts/${postId}`,
        {
          status: 'failed',
          error_message: error.message,
        }
      ).catch(console.error);
      
      throw error;
    }
  },
  {
    connection: redis,
    concurrency: 2,
    removeOnComplete: { count: 50 },
    removeOnFail: { count: 25 },
  }
);

// Redis connection event handlers
redis.on('connect', () => {
  console.log('Connected to Redis');
});

redis.on('error', (err) => {
  console.error('Redis connection error:', err);
});

redis.on('ready', () => {
  console.log('Redis connection ready');
});

redis.on('close', () => {
  console.log('Redis connection closed');
});

// Error handling for workers
postWorker.on('completed', (job) => {
  console.log(`Job ${job.id} completed successfully`);
});

postWorker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err.message);
});

postWorker.on('error', (err) => {
  console.error('Post worker error:', err);
});

twitterWorker.on('completed', (job) => {
  console.log(`Twitter job ${job.id} completed successfully`);
});

twitterWorker.on('failed', (job, err) => {
  console.error(`Twitter job ${job?.id} failed:`, err.message);
});

linkedinWorker.on('completed', (job) => {
  console.log(`LinkedIn job ${job.id} completed successfully`);
});

linkedinWorker.on('failed', (job, err) => {
  console.error(`LinkedIn job ${job?.id} failed:`, err.message);
});

instagramWorker.on('completed', (job) => {
  console.log(`Instagram job ${job.id} completed successfully`);
});

instagramWorker.on('failed', (job, err) => {
  console.error(`Instagram job ${job?.id} failed:`, err.message);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('Shutting down workers...');
  await postWorker.close();
  await twitterWorker.close();
  await linkedinWorker.close();
  await instagramWorker.close();
  await postQueue.close();
  await redis.disconnect();
  process.exit(0);
});

console.log('Worker scheduler started successfully');
console.log('Redis URL:', process.env.REDIS_URL || 'redis://redis:6379');
console.log('API Gateway URL:', API_GATEWAY_URL);
console.log('Automation Backend URL:', process.env.AUTOMATION_BACKEND_URL || 'http://automation-backend:8001');

// Export queue for other modules to use
export { postQueue };
