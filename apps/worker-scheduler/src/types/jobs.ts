// apps/worker-scheduler/src/types/jobs.ts - Job Type Definitions
export interface BaseJobData {
  postId: string;
  userId: string;
  accountId: string;
  content: string;
  scheduledFor?: string;
}

export interface SocialMediaJobData extends BaseJobData {
  platform: 'twitter' | 'linkedin' | 'instagram';
  imageUrl?: string;
  hashtags?: string[];
  mentions?: string[];
}

export interface JobResult {
  success: boolean;
  postId: string;
  platform: string;
  publishedAt?: string;
  error?: string;
  platformResponse?: any;
}

export interface QueueConfig {
  name: string;
  concurrency: number;
  removeOnComplete: number;
  removeOnFail: number;
}

export const QUEUE_CONFIGS: Record<string, QueueConfig> = {
  'post-queue': {
    name: 'post-queue',
    concurrency: 5,
    removeOnComplete: 100,
    removeOnFail: 50,
  },
  'twitter-queue': {
    name: 'twitter-queue',
    concurrency: 3,
    removeOnComplete: 50,
    removeOnFail: 25,
  },
  'linkedin-queue': {
    name: 'linkedin-queue',
    concurrency: 3,
    removeOnComplete: 50,
    removeOnFail: 25,
  },
  'instagram-queue': {
    name: 'instagram-queue',
    concurrency: 2,
    removeOnComplete: 50,
    removeOnFail: 25,
  },
};