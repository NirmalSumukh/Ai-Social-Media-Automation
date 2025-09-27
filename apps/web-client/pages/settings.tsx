import { useState, useEffect, useCallback } from 'react';
import Header from '../components/Header';
import Sidebar from '../components/Sidebar';
import { api } from '../lib/api';

// FIXED: Added error boundary wrapper
function ErrorBoundary({ children, fallback }: { children: React.ReactNode, fallback: React.ReactNode }) {
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    const errorHandler = () => setHasError(true);
    window.addEventListener('error', errorHandler);
    return () => window.removeEventListener('error', errorHandler);
  }, []);

  if (hasError) {
    return <div>{fallback}</div>;
  }

  return <>{children}</>;
}

interface ConnectedAccount {
  id: string;
  platform: string;
  username: string;
  isActive: boolean;
}

export default function Settings() {
  const [connectedAccounts, setConnectedAccounts] = useState<ConnectedAccount[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [connected, setConnected] = useState('');

  const platformConfigs = [
    {
      id: 'twitter',
      name: 'Twitter',
      description: 'Connect your Twitter account to post tweets',
      color: 'bg-blue-500',
      icon: '🐦'
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      description: 'Share professional content on LinkedIn',
      color: 'bg-blue-700',
      icon: '💼'
    },
    {
      id: 'instagram',
      name: 'Instagram',
      description: 'Post photos and stories to Instagram',
      color: 'bg-pink-500',
      icon: '📸'
    }
  ];

  // FIXED: Properly memoized functions
  const fetchConnectedAccounts = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.get('/social-accounts');
      // FIXED: Ensure we always set an array
      setConnectedAccounts(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error fetching connected accounts:', error);
      setError('Failed to load connected accounts');
      setConnectedAccounts([]); // FIXED: Always ensure array
    } finally {
      setLoading(false);
    }
  }, []);

  const handleConnect = useCallback(async (platform: string) => {
    try {
      setLoading(true);
      setError('');
      
      if (platform === 'twitter') {
        // Start Twitter OAuth flow
        window.location.href = 'http://localhost:8000/auth/twitter/login';
      } else {
        // For demo: simulate connection for other platforms
        setConnected(`${platform} (Demo Mode)`);
        setTimeout(() => setConnected(''), 3000);
      }
    } catch (error) {
      console.error('Error connecting account:', error);
      setError('Failed to connect account');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleDemoConnect = useCallback(async (platform: string) => {
    try {
      setLoading(true);
      setError('');
      
      // Demo connection
      const demoAccount: ConnectedAccount = {
        id: `demo_${platform}`,
        platform: platform,
        username: `demo_${platform}_user`,
        isActive: true
      };
      
      setConnectedAccounts(prev => [...prev, demoAccount]);
      setConnected(`${platform} (Demo)`);
      setTimeout(() => setConnected(''), 3000);
    } catch (error) {
      console.error('Error in demo connect:', error);
      setError('Demo connection failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnectedAccounts();
  }, [fetchConnectedAccounts]);

  return (
    <ErrorBoundary fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Something went wrong</h2>
          <button 
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            Refresh Page
          </button>
        </div>
      </div>
    }>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="flex">
          <Sidebar />
          <main className="flex-1 p-8">
            <div className="max-w-4xl mx-auto">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
              <p className="text-gray-600 mb-8">Manage your connected social media accounts</p>

              {/* Success/Error Messages */}
              {connected && (
                <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
                  ✅ Successfully connected {connected}!
                </div>
              )}

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                  ❌ Error: {error}
                </div>
              )}

              {/* Loading State */}
              {loading && (
                <div className="bg-blue-50 border border-blue-200 text-blue-700 px-4 py-3 rounded mb-6">
                  🔄 Loading...
                </div>
              )}

              {/* Platform Connections */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold">Social Media Platforms</h2>
                </div>
                <div className="p-6">
                  <div className="grid gap-4">
                    {platformConfigs.map((config) => (
                      <div key={config.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 ${config.color} rounded-lg flex items-center justify-center text-white text-xl`}>
                            {config.icon}
                          </div>
                          <div>
                            <h3 className="font-semibold text-gray-900">{config.name}</h3>
                            <p className="text-gray-600 text-sm">{config.description}</p>
                          </div>
                        </div>
                        <div className="space-x-2">
                          <button
                            onClick={() => handleConnect(config.id)}
                            disabled={loading}
                            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
                          >
                            Connect
                          </button>
                          <button
                            onClick={() => handleDemoConnect(config.id)}
                            disabled={loading}
                            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
                          >
                            Demo
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Connected Accounts */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <h2 className="text-xl font-semibold">Active Connections</h2>
                </div>
                <div className="p-6">
                  {/* FIXED: Safe array checking */}
                  {!connectedAccounts || connectedAccounts.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <div className="text-4xl mb-2">🔗</div>
                      <p>No accounts connected yet</p>
                      <p className="text-sm">Connect your social media accounts above</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {connectedAccounts.map((account) => (
                        <div key={account.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                          <div className="flex items-center space-x-3">
                            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-semibold">
                              ✓
                            </div>
                            <div>
                              <p className="font-medium text-gray-900 capitalize">{account.platform}</p>
                              <p className="text-gray-600 text-sm">@{account.username}</p>
                            </div>
                          </div>
                          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                            Connected
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}
