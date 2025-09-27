// apps/web-client/components/Sidebar.tsx - Navigation Sidebar Component (Fixed)
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../lib/api';
import {
  HomeIcon,
  CalendarIcon,
  ChatBubbleLeftIcon,
  Cog6ToothIcon,
  PlusIcon,
  UserGroupIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeSolid,
  CalendarIcon as CalendarSolid,
  ChatBubbleLeftIcon as ChatSolid,
  Cog6ToothIcon as CogSolid,
} from '@heroicons/react/24/solid';

interface ConnectedAccount {
  id: string;
  platform: 'twitter' | 'linkedin' | 'instagram';
  username: string;
  isActive: boolean;
}

const navigation = [
  { 
    name: 'Dashboard', 
    href: '/dashboard', 
    icon: HomeIcon, 
    iconSolid: HomeSolid,
    description: 'Overview & Analytics'
  },
  { name: 'New Post', 
    href: '/new-post', 
    icon: PlusIcon },
  { 
    name: 'Calendar', 
    href: '/calendar', 
    icon: CalendarIcon, 
    iconSolid: CalendarSolid,
    description: 'Schedule Posts'
  },
  { 
    name: 'AI Assistant', 
    href: '/chatbot', 
    icon: ChatBubbleLeftIcon, 
    iconSolid: ChatSolid,
    description: 'Content Creation'
  },
  { 
    name: 'Analytics', 
    href: '/analytics', 
    icon: ChartBarIcon, 
    iconSolid: ChartBarIcon,
    description: 'Performance Insights'
  },
  { 
    name: 'Settings', 
    href: '/settings', 
    icon: Cog6ToothIcon, 
    iconSolid: CogSolid,
    description: 'Account Management'
  },
];

const quickActions = [
  { name: 'New Post', icon: PlusIcon, action: 'create-post' },
  { name: 'Connect Account', icon: UserGroupIcon, action: 'connect-account' },
];

export default function Sidebar() {
  const router = useRouter();
  const { user } = useAuth();
  const [connectedAccounts, setConnectedAccounts] = useState<ConnectedAccount[]>([]);
  const [notifications, setNotifications] = useState(0);
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    fetchConnectedAccounts();
    fetchNotifications();
  }, []);

  const fetchConnectedAccounts = async () => {
    try {
      const response = await api.get('/social-accounts');
      setConnectedAccounts(response.data);
    } catch (error) {
      console.error('Error fetching connected accounts:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications/count');
      setNotifications(response.data.count);
    } catch (error) {
      console.error('Error fetching notifications:', error);
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

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'create-post':
        router.push('/calendar?action=create');
        break;
      case 'connect-account':
        router.push('/settings?tab=accounts');
        break;
      default:
        break;
    }
  };

  return (
    <div className={`${isCollapsed ? 'w-16' : 'w-64'} bg-gray-900 text-white flex flex-col h-full transition-all duration-300 ease-in-out`}>
      {/* Header */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div>
              <h2 className="text-xl font-bold text-white">AI Social</h2>
              <p className="text-xs text-gray-400 mt-1">Media Platform</p>
            </div>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
          >
            {isCollapsed ? (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      {!isCollapsed && (
        <div className="px-4 py-4 border-b border-gray-800">
          <div className="space-y-2">
            {quickActions.map((action) => (
              <button
                key={action.name}
                onClick={() => handleQuickAction(action.action)}
                className="w-full flex items-center px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                <action.icon className="w-4 h-4 mr-2" />
                {action.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6">
        <div className="space-y-2">
          {navigation.map((item) => {
            const isActive = router.pathname === item.href;
            const IconComponent = isActive ? item.iconSolid ?? item.icon : item.icon ?? item.iconSolid;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center px-3 py-3 text-sm rounded-lg transition-colors group ${
                  isActive 
                    ? 'bg-blue-600 text-white' 
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                {IconComponent ? (
                  <IconComponent className={`${isCollapsed ? 'w-6 h-6' : 'w-5 h-5 mr-3'} ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'}`} />
                ) : null}
                {!isCollapsed && (
                  <div>
                    <div className="font-medium">{item.name}</div>
                    <div className="text-xs text-gray-400 group-hover:text-gray-300">
                      {item.description}
                    </div>
                  </div>
                )}
                {item.name === 'Dashboard' && notifications > 0 && (
                  <span className="ml-auto bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                    {notifications}
                  </span>
                )}
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Connected Accounts */}
      {!isCollapsed && (
        <div className="px-4 py-4 border-t border-gray-800">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Connected Accounts
          </h3>
          <div className="space-y-2">
            {connectedAccounts.length === 0 ? (
              <div className="text-sm text-gray-500 text-center py-4">
                <UserGroupIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No accounts connected</p>
                <button
                  onClick={() => router.push('/settings?tab=accounts')}
                  className="text-blue-400 hover:text-blue-300 text-xs mt-1"
                >
                  Connect your first account
                </button>
              </div>
            ) : (
              connectedAccounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center justify-between p-2 rounded-lg bg-gray-800"
                >
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${getPlatformColor(account.platform)} mr-2`} />
                    <span className="text-sm text-white">@{account.username}</span>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${account.isActive ? 'bg-green-400' : 'bg-gray-600'}`} />
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* User Info */}
      <div className="px-4 py-4 border-t border-gray-800">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mr-3">
            <span className="text-sm font-medium text-white">
              {user?.email?.charAt(0).toUpperCase()}
            </span>
          </div>
          {!isCollapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.email}
              </p>
              <p className="text-xs text-gray-400">
                {connectedAccounts.length} account{connectedAccounts.length !== 1 ? 's' : ''} connected
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Notifications Indicator (Collapsed) */}
      {isCollapsed && notifications > 0 && (
        <div className="absolute top-4 right-2">
          <span className="bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
            {notifications > 9 ? '9+' : notifications}
          </span>
        </div>
      )}
    </div>
  );
}
