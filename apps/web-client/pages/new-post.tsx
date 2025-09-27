import { useState, useCallback } from 'react';
import { useRouter } from 'next/router';
import Image from 'next/image';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { api } from '../lib/api';

interface MediaFile {
  file: File;
  url: string;
  type: 'image' | 'video';
}

export default function NewPost() {
  const router = useRouter();
  const [content, setContent] = useState('');
  const [platform, setPlatform] = useState('twitter');
  const [hashtags, setHashtags] = useState('');
  const [media, setMedia] = useState<MediaFile | null>(null);
  const [isScheduled, setIsScheduled] = useState(false);
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [loading, setLoading] = useState(false);

  // Character limits by platform
  const characterLimits = {
    twitter: 280,
    linkedin: 3000,
    instagram: 2200
  };

  const currentLimit = characterLimits[platform as keyof typeof characterLimits];
  const remainingChars = currentLimit - content.length;

  const handleMediaUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Check file type
    const isImage = file.type.startsWith('image/');
    const isVideo = file.type.startsWith('video/');
    
    if (!isImage && !isVideo) {
      alert('Please select an image or video file');
      return;
    }

    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    const url = URL.createObjectURL(file);
    setMedia({
      file,
      url,
      type: isImage ? 'image' : 'video'
    });
  }, []);

  const removeMedia = useCallback(() => {
    if (media) {
      URL.revokeObjectURL(media.url);
      setMedia(null);
    }
  }, [media]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!content.trim()) {
      alert('Please enter some content');
      return;
    }

    if (content.length > currentLimit) {
      alert(`Content exceeds ${currentLimit} character limit`);
      return;
    }

    setLoading(true);

    try {
      let mediaUrl = '';
      
      // Upload media if present
      if (media) {
        const formData = new FormData();
        formData.append('media', media.file);
        
        try {
          const mediaResponse = await api.post('/posts/upload-media', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          mediaUrl = mediaResponse.data.url;
        } catch (error) {
          console.error('Media upload failed:', error);
          // Continue without media for demo
        }
      }

      // Create post data
      const postData = {
        content: content.trim(),
        platform,
        post_type: media ? media.type : 'text',
        media_url: mediaUrl,
        hashtags: hashtags ? hashtags.split(' ').filter(tag => tag.startsWith('#')) : [],
        scheduled_at: isScheduled && scheduledDate && scheduledTime 
          ? new Date(`${scheduledDate}T${scheduledTime}`).toISOString() 
          : null
      };

      const response = await api.post('/posts', postData);
      
      if (response.data) {
        alert(isScheduled ? 'Post scheduled successfully!' : 'Post created successfully!');
        router.push('/dashboard');
      }

    } catch (error) {
      console.error('Error creating post:', error);
      alert('Failed to create post. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePublishNow = async () => {
    if (!content.trim()) {
      alert('Please enter some content');
      return;
    }

    setLoading(true);

    try {
      const postData = {
        content: content.trim(),
        platform,
        post_type: media ? media.type : 'text',
        media_url: media?.url || '',
        hashtags: hashtags ? hashtags.split(' ').filter(tag => tag.startsWith('#')) : []
      };

      const createResponse = await api.post('/posts', postData);
      
      if (createResponse.data?.id) {
        // Immediately publish
        await api.post(`/posts/${createResponse.data.id}/publish`);
        alert('Post published successfully!');
        router.push('/dashboard');
      }

    } catch (error) {
      console.error('Error publishing post:', error);
      alert('Failed to publish post. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto">
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-gray-900">Create New Post</h1>
              <p className="text-gray-600 mt-1">Create and schedule your social media content</p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
              {/* Platform Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Platform
                </label>
                <div className="flex space-x-4">
                  {[
                    { id: 'twitter', name: 'Twitter', color: 'bg-blue-500', limit: 280 },
                    { id: 'linkedin', name: 'LinkedIn', color: 'bg-blue-700', limit: 3000 },
                    { id: 'instagram', name: 'Instagram', color: 'bg-pink-500', limit: 2200 }
                  ].map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setPlatform(p.id)}
                      className={`flex items-center px-4 py-2 rounded-lg border-2 transition-colors ${
                        platform === p.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-300 hover:border-gray-400'
                      }`}
                    >
                      <div className={`w-4 h-4 ${p.color} rounded mr-2`}></div>
                      <span className="font-medium">{p.name}</span>
                      <span className="text-xs text-gray-500 ml-2">({p.limit} chars)</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Content Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Content
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder={platform === 'twitter' ? "What's happening? (Max 280 characters)" : "Share your thoughts..."}
                  className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                  maxLength={currentLimit}
                />
                <div className="flex justify-between items-center mt-2">
                  <span className="text-sm text-gray-500">
                    {platform === 'twitter' && '🐦 Perfect for Twitter\'s character limit'}
                    {platform === 'linkedin' && '💼 Professional content for LinkedIn'}
                    {platform === 'instagram' && '📸 Engaging content for Instagram'}
                  </span>
                  <span className={`text-sm font-medium ${
                    remainingChars < 20 ? 'text-red-500' : remainingChars < 50 ? 'text-yellow-500' : 'text-gray-500'
                  }`}>
                    {remainingChars}/{currentLimit}
                  </span>
                </div>
                
                {/* Twitter Character Warning */}
                {platform === 'twitter' && content.length > 250 && (
                  <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
                    ⚠️ Close to Twitter&#39;s 280 character limit!
                  </div>
                )}
              </div>

              {/* Media Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Media (Optional)
                </label>
                {!media ? (
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <input
                      type="file"
                      accept="image/*,video/*"
                      onChange={handleMediaUpload}
                      className="hidden"
                      id="media-upload"
                    />
                    <label
                      htmlFor="media-upload"
                      className="cursor-pointer flex flex-col items-center"
                    >
                      <svg className="w-8 h-8 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                      <span className="text-sm text-gray-600 font-medium">Upload image or video</span>
                      <span className="text-xs text-gray-400 mt-1">JPG, PNG, MP4, MOV • Max 10MB</span>
                    </label>
                  </div>
                ) : (
                  <div className="relative rounded-lg overflow-hidden">
                    {media.type === 'image' ? (
                      <div className="relative w-full h-48">
                        <Image
                          src={media.url}
                          alt="Upload preview"
                          fill
                          className="object-cover"
                          unoptimized // Required for blob URLs
                        />
                      </div>
                    ) : (
                      <video
                        src={media.url}
                        className="w-full h-48 object-cover"
                        controls
                        preload="metadata"
                      />
                    )}
                    <button
                      type="button"
                      onClick={removeMedia}
                      className="absolute top-2 right-2 bg-red-500 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg"
                      title="Remove media"
                    >
                      ×
                    </button>
                  </div>
                )}
              </div>

              {/* Hashtags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Hashtags (Optional)
                </label>
                <input
                  type="text"
                  value={hashtags}
                  onChange={(e) => setHashtags(e.target.value)}
                  placeholder="#AI #SocialMedia #Marketing"
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Separate hashtags with spaces</p>
              </div>

              {/* Scheduling */}
              <div className="border-t pt-4">
                <div className="flex items-center mb-3">
                  <input
                    type="checkbox"
                    id="schedule"
                    checked={isScheduled}
                    onChange={(e) => setIsScheduled(e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="schedule" className="ml-2 text-sm font-medium text-gray-700">
                    📅 Schedule this post for later
                  </label>
                </div>
                
                {isScheduled && (
                  <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded-lg">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Date</label>
                      <input
                        type="date"
                        value={scheduledDate}
                        onChange={(e) => setScheduledDate(e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        placeholder="Select date"
                        title="Select the scheduled date"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Time</label>
                      <input
                        type="time"
                        value={scheduledTime}
                        onChange={(e) => setScheduledTime(e.target.value)}
                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-sm"
                        placeholder="Select time"
                        title="Select the scheduled time"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-4 pt-4 border-t">
                <button
                  type="button"
                  onClick={() => router.push('/dashboard')}
                  className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                
                <button
                  type="button"
                  onClick={handlePublishNow}
                  disabled={loading || !content.trim()}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Publishing...' : '🚀 Publish Now'}
                </button>

                <button
                  type="submit"
                  disabled={loading || !content.trim() || (isScheduled && (!scheduledDate || !scheduledTime))}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {loading ? 'Saving...' : isScheduled ? '⏰ Schedule Post' : '💾 Save as Draft'}
                </button>
              </div>
            </form>
          </div>
        </main>
      </div>
    </div>
  );
}
