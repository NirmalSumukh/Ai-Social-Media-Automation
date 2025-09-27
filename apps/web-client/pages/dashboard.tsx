// apps/web-client/pages/dashboard.tsx - Post Overview & Stats Dashboard
import { useState, useEffect } from 'react';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import PostCard from '../components/PostCard';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';

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

interface Stats {
  total_posts: number; // FIXED: Changed from totalPosts to total_posts
  scheduled_posts: number; // FIXED: Changed from scheduledPosts to scheduled_posts  
  published_posts: number; // FIXED: Changed from publishedPosts to published_posts
  draft_posts: number;
  failed_posts: number;
}

export default function Dashboard() {
  const [posts, setPosts] = useState<Post[]>([]); // FIXED: Added proper typing and default empty array
  const [stats, setStats] = useState<Stats>({
    total_posts: 0, // FIXED: Match backend field names
    scheduled_posts: 0,
    published_posts: 0,
    draft_posts: 0,
    failed_posts: 0
  });
  const [loading, setLoading] = useState(true); // FIXED: Added loading state
  const [error, setError] = useState<string | null>(null); // FIXED: Added error state

  const { user } = useAuth();

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchPosts(), fetchStats()]);
      setLoading(false);
    };
    loadData();
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await api.get('/posts');
      // FIXED: Ensure we always set an array, even if response is null/undefined
      setPosts(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setError('Failed to load posts');
      setPosts([]); // FIXED: Always ensure posts is an array
    }
  };

  const fetchStats = async () => {
    try {
      const response = await api.get('/posts/stats');
      if (response.data) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
      setError('Failed to load statistics');
    }
  };

  // FIXED: Add loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2">Loading...</span>
            </div>
          </main>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-2">Welcome back, {user?.email || 'User'}</p>
          </div>

          {/* FIXED: Added error display */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
              {error}
            </div>
          )}

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="text-3xl font-bold text-gray-900">{stats.total_posts}</div>
              <div className="text-gray-600">Total Posts</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="text-3xl font-bold text-blue-600">{stats.scheduled_posts}</div>
              <div className="text-gray-600">Scheduled</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="text-3xl font-bold text-green-600">{stats.published_posts}</div>
              <div className="text-gray-600">Published</div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <div className="text-3xl font-bold text-red-600">{stats.draft_posts}</div>
              <div className="text-gray-600">Drafts</div>
            </div>
          </div>

          {/* Recent Posts */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Recent Posts</h2>
            </div>
            <div className="p-6">
              {/* FIXED: Safe array checking and mapping */}
              {!posts || posts.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-lg mb-2">📝</div>
                  <p className="text-gray-600">No posts yet. Create your first post!</p>
                  <button 
                    onClick={() => window.location.href = '/new-post'}
                    className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Create Post
                  </button>
                </div>
              ) : (
                <div className="grid gap-4">
                  {posts.slice(0, 6).map((post) => (
                    <PostCard key={post.id} post={post} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
