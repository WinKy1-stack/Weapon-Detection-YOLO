import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Scan, 
  AlertTriangle, 
  BarChart3, 
  LogOut,
  Shield
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigation = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Detection', path: '/detection', icon: Scan },
    { name: 'Alerts', path: '/alerts', icon: AlertTriangle },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-slate-800 border-r border-slate-700">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 p-6 border-b border-slate-700">
            <Shield className="w-8 h-8 text-primary-500" />
            <div>
              <h1 className="text-xl font-bold text-white">Weapon Detection</h1>
              <p className="text-sm text-gray-400">Security System</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-slate-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* User Info */}
          <div className="p-4 border-t border-slate-700">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 bg-primary-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">
                  {user?.email?.[0].toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-gray-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 min-h-screen">
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
