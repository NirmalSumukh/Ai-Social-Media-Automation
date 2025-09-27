// apps/web-client/components/PostCard.tsx - Post Display Card Component
import { useState } from 'react';
import { useRouter } from 'next/router';
import { 
  ClockIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  PencilIcon,
  TrashIcon,
  ShareIcon 
} from '@heroicons/react/24/outline';

// FIXED: Updated interface to match backend structure
interface Post {
  id: string;
  content: string;
  platform: string; // FIXED: Changed from platforms to platform
  scheduled_at: string | null; // FIXED: Changed from scheduledFor to scheduled_at
  status: string;
  created_at: string; // FIXED: Changed from createdAt to created_at
  title?: string;
  hashtags?: string[];
  media_url?: string;
}

interface PostCardProps {
  post: Post;
  onUpdate?: () => void;
}

export default function PostCard({ post, onUpdate }: PostCardProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // Helper functions
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800';
      case 'scheduled': return 'bg-blue-100 text-blue-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'failed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'published': return <CheckCircleIcon className="w-4 h-4" />;
      case 'scheduled': return <ClockIcon className="w-4 h-4" />;
      case 'failed': return <XCircleIcon className="w-4 h-4" />;
      default: return <PencilIcon className="w-4 h-4" />;
    }
  };

  const getPlatformColor = (platform: string) => {
    switch (platform) {
      case 'twitter': return 'bg-blue-500';
      case 'linkedin': return 'bg-blue-700';
      case 'instagram': return 'bg-pink-500';
      default: return 'bg-gray-500';
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not scheduled';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const handleEdit = () => {
    router.push(`/new-post?edit=${post.id}`);
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this post?')) return;
    
    setLoading(true);
    try {
      // Add delete API call here when needed
      console.log('Delete post:', post.id);
      onUpdate?.();
    } catch (error) {
      console.error('Failed to delete post:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = () => {
    // Add share functionality here
    console.log('Share post:', post.id);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          {/* Platform indicator */}
          <div className={`w-3 h-3 rounded-full ${getPlatformColor(post.platform)}`} />
          <div>
            <p className="font-medium text-gray-900 capitalize">{post.platform}</p>
            <p className="text-xs text-gray-500">
              Created: {formatDate(post.created_at)}
            </p>
          </div>
        </div>

        {/* Status badge */}
        <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(post.status)}`}>
          {getStatusIcon(post.status)}
          <span className="ml-1 capitalize">{post.status}</span>
        </div>
      </div>

      {/* Content */}
      <div className="mb-3">
        {post.title && (
          <h3 className="font-medium text-gray-900 mb-1">{post.title}</h3>
        )}
        <p className="text-gray-700 text-sm line-clamp-3">
          {post.content}
        </p>
        
        {/* Hashtags */}
        {post.hashtags && post.hashtags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {post.hashtags.slice(0, 3).map((tag, index) => (
              <span 
                key={index} 
                className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded"
              >
                #{tag}
              </span>
            ))}
            {post.hashtags.length > 3 && (
              <span className="text-xs text-gray-500">
                +{post.hashtags.length - 3} more
              </span>
            )}
          </div>
        )}

        {/* Media indicator */}
        {post.media_url && (
          <div className="mt-2 text-xs text-gray-500 flex items-center">
            <span>📎 Media attached</span>
          </div>
        )}
      </div>

      {/* Scheduled time */}
      {post.scheduled_at && (
        <div className="mb-3 text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
          ⏰ Scheduled: {formatDate(post.scheduled_at)}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-100">
        <div className="flex space-x-2">
          <button
            onClick={handleEdit}
            disabled={loading}
            className="flex items-center px-2 py-1 text-xs text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          >
            <PencilIcon className="w-3 h-3 mr-1" />
            Edit
          </button>
          
          <button
            onClick={handleShare}
            disabled={loading}
            className="flex items-center px-2 py-1 text-xs text-gray-600 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
          >
            <ShareIcon className="w-3 h-3 mr-1" />
            Share
          </button>
        </div>

        <button
          onClick={handleDelete}
          disabled={loading}
          className="flex items-center px-2 py-1 text-xs text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
        >
          <TrashIcon className="w-3 h-3 mr-1" />
          {loading ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </div>
  );
}
