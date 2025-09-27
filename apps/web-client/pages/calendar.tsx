// apps/web-client/pages/calendar.tsx - Full-Screen Calendar Scheduler (Fixed)
import { useState, useEffect } from 'react';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import CalendarGrid from '../components/CalendarGrid';
import { api } from '../lib/api';

interface Post {
  id: string;
  content: string;
  platforms: string[];
  scheduledFor: string;
  status: string;
}

export default function Calendar() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [selectedDate, setSelectedDate] = useState(new Date());

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await api.get('/posts');
      setPosts(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };

  const handleCreatePost = () => {
    // Navigate to create post with the selected date
    window.location.href = `/chatbot?date=${selectedDate.toISOString()}`;
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto p-6">
          <div className="mb-6 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Content Calendar</h1>
            <button
              onClick={handleCreatePost}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Schedule Post
            </button>
          </div>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            <CalendarGrid 
              posts={posts}
              selectedDate={selectedDate}
              onDateSelect={setSelectedDate}
            />
          </div>
        </main>
      </div>
    </div>
  );
}
