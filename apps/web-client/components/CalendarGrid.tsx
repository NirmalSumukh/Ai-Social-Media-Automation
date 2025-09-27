// apps/web-client/components/CalendarGrid.tsx - Calendar Interface Component (Fixed)
import { useState } from 'react';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, isToday } from 'date-fns';

interface Post {
  id: string;
  content: string;
  platforms: string[];
  scheduledFor: string;
  status: string;
}

interface CalendarGridProps {
  posts: Post[];
  selectedDate: Date;
  onDateSelect: (date: Date) => void;
}

export default function CalendarGrid({ posts, selectedDate, onDateSelect }: CalendarGridProps) {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const days = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const getPostsForDate = (date: Date) => {
    return posts.filter(post => 
      isSameDay(new Date(post.scheduledFor), date)
    );
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const handleDayClick = (day: Date) => {
    onDateSelect(day);
  };

  const handlePostClick = (post: Post, event: React.MouseEvent) => {
    event.stopPropagation();
    // Navigate to edit post
    window.location.href = `/chatbot?edit=${post.id}`;
  };

  return (
    <div className="p-6">
      {/* Calendar Header */}
      <div className="flex justify-between items-center mb-6">
        <button
          onClick={prevMonth}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Previous month"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 className="text-xl font-semibold">
          {format(currentMonth, 'MMMM yyyy')}
        </h2>
        <button
          onClick={nextMonth}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          aria-label="Next month"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Days of Week */}
      <div className="grid grid-cols-7 gap-px mb-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="p-3 text-center text-sm font-medium text-gray-500">
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Days */}
      <div className="grid grid-cols-7 gap-px bg-gray-200 rounded-lg overflow-hidden">
        {days.map(day => {
          const dayPosts = getPostsForDate(day);
          const isSelected = isSameDay(day, selectedDate);
          const isCurrentDay = isToday(day);

          return (
            <div
              key={day.toString()}
              onClick={() => handleDayClick(day)}
              className={`bg-white p-3 min-h-[120px] cursor-pointer hover:bg-gray-50 transition-colors ${
                isSelected ? 'ring-2 ring-blue-500' : ''
              } ${isCurrentDay ? 'bg-blue-50' : ''}`}
            >
              <div className={`text-sm font-medium mb-2 ${
                isCurrentDay ? 'text-blue-600' : 'text-gray-900'
              }`}>
                {format(day, 'd')}
              </div>
              
              <div className="space-y-1">
                {dayPosts.slice(0, 3).map(post => (
                  <div
                    key={post.id}
                    onClick={(e) => handlePostClick(post, e)}
                    className={`text-xs px-2 py-1 rounded truncate cursor-pointer hover:opacity-80 ${
                      post.status === 'published' ? 'bg-green-100 text-green-800' :
                      post.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                      post.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}
                    title={post.content}
                  >
                    {post.content.substring(0, 20)}...
                  </div>
                ))}
                {dayPosts.length > 3 && (
                  <div className="text-xs text-gray-500 px-2">
                    +{dayPosts.length - 3} more
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Date Info */}
      {selectedDate && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {format(selectedDate, 'EEEE, MMMM d, yyyy')}
          </h3>
          <div className="text-sm text-gray-600">
            {getPostsForDate(selectedDate).length === 0 ? (
              <p>No posts scheduled for this date.</p>
            ) : (
              <p>{getPostsForDate(selectedDate).length} post{getPostsForDate(selectedDate).length !== 1 ? 's' : ''} scheduled</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
