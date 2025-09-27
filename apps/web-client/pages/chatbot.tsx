// apps/web-client/pages/chatbot.tsx - AI Assistant UI (Fixed)
import { useState, useEffect, useRef } from 'react';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import { api } from '../lib/api';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

interface ChatHistoryResponse {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: string; // API returns string, we'll convert to Date
}

interface ChatMessageResponse {
  response: string;
  suggestions?: string[];
}

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load chat history
    loadChatHistory();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const response = await api.get('/chatbot/history');
      const historyData: ChatHistoryResponse[] = response.data;
      
      setMessages(historyData.map((msg) => ({
        id: msg.id,
        content: msg.content,
        isBot: msg.isBot,
        timestamp: new Date(msg.timestamp)
      })));
    } catch (error) {
      console.error('Error loading chat history:', error);
      // Initialize with welcome message if no history
      const welcomeMessage: Message = {
        id: 'welcome-1',
        content: "Hi! I'm your AI content assistant. Tell me about your business and I'll help you create engaging social media posts. What industry are you in?",
        isBot: true,
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await api.post('/chatbot/message', {
        message: inputValue
      });

      const responseData: ChatMessageResponse = response.data;

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: responseData.response,
        isBot: true,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);

      // Handle suggestions if provided
      if (responseData.suggestions && responseData.suggestions.length > 0) {
        const suggestionsMessage: Message = {
          id: (Date.now() + 2).toString(),
          content: `Here are some suggestions:\n• ${responseData.suggestions.join('\n• ')}`,
          isBot: true,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, suggestionsMessage]);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again. Make sure your backend services are running.',
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
  };

  const clearChat = () => {
    setMessages([]);
    loadChatHistory();
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        
        <main className="flex-1 overflow-hidden p-6">
          <div className="h-full bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Content Assistant</h1>
                <p className="text-gray-600 mt-1">Tell me about your business to create personalized content</p>
              </div>
              <button
                onClick={clearChat}
                className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1 border border-gray-300 rounded"
              >
                Clear Chat
              </button>
            </div>
            
            <ChatWindow 
              messages={messages}
              isLoading={isLoading}
              messagesEndRef={messagesEndRef}
            />

            <div className="p-4 border-t border-gray-200">
              <div className="flex space-x-2">
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me to create content for your business..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={2}
                  disabled={isLoading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? 'Sending...' : 'Send'}
                </button>
              </div>
              
              {/* Quick action buttons */}
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  onClick={() => handleSuggestionClick("Create a LinkedIn post about my business")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  LinkedIn Post
                </button>
                <button
                  onClick={() => handleSuggestionClick("Generate a Twitter thread about my services")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Twitter Thread
                </button>
                <button
                  onClick={() => handleSuggestionClick("Create an Instagram caption for my product")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Instagram Caption
                </button>
                <button
                  onClick={() => handleSuggestionClick("Help me with content strategy")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full transition-colors"
                >
                  Content Strategy
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
