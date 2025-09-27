// apps/web-client/components/Header.tsx - Navigation Header
import { useAuth } from '../hooks/useAuth';
import { useRouter } from 'next/router';
import { BellIcon, UserCircleIcon } from '@heroicons/react/24/outline';

export function Header() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* REMOVED: This was the extra "AI Social" text appearing outside the sidebar */}
        {/* Keep this section empty or add breadcrumbs if needed */}
        <div className="flex-1">
          {/* Optional: Add breadcrumbs or page title here instead of duplicate branding */}
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
            title="Notifications"
          >
            <BellIcon className="w-6 h-6" />
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <UserCircleIcon className="w-8 h-8 text-gray-400" />
              <div className="text-left">
                {/* <div className="text-sm font-medium text-gray-900">{user?.full_name || 'User'}</div> */}
                <div className="text-xs text-gray-500">{user?.email}</div>
              </div>
            </div>
            
            <button
              onClick={handleLogout}
              className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1 rounded-md hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Header;
