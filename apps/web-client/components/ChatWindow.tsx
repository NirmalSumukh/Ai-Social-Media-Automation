// apps/web-client/components/ChatWindow.tsx - Chat Interface Component
import { format } from 'date-fns';

interface Message {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
}

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  messagesEndRef: React.RefObject<HTMLDivElement>;
}

export default function ChatWindow({ messages, isLoading, messagesEndRef }: ChatWindowProps) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      {messages.length === 0 && (
        <div className="text-center py-8">
          <div className="bg-blue-50 rounded-lg p-6 max-w-md mx-auto">
            <h3 className="text-lg font-medium text-blue-900 mb-2">Welcome to your AI Assistant!</h3>
            <p className="text-blue-700 text-sm">
              I can help you create engaging content for your social media platforms. 
              Tell me about your business, target audience, or ask me to generate posts!
            </p>
          </div>
        </div>
      )}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
        >
          <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
            message.isBot 
              ? 'bg-gray-100 text-gray-900' 
              : 'bg-blue-600 text-white'
          }`}>
            <div className="whitespace-pre-wrap text-sm">
              {message.content}
            </div>
            <div className={`text-xs mt-1 ${
              message.isBot ? 'text-gray-500' : 'text-blue-100'
            }`}>
              {format(message.timestamp, 'h:mm a')}
            </div>
          </div>
        </div>
      ))}

      {isLoading && (
        <div className="flex justify-start">
          <div className="bg-gray-100 rounded-lg px-4 py-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce bounceDelay" />
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce bounceDelay" />
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}