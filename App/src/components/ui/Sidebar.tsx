import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mic, Shield, Users, LogOut, Settings, Home, UserPlus as UserPlusIcon } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Navigation items based on user role
  const navigation =
    user?.role === 'user'
      ? [
          // Regular user navigation
          {
            id: 'dashboard',
            label: 'Dashboard',
            href: '/dashboard',
            icon: Home,
          },
          {
            id: 'enrollment',
            label: 'Registro de Voz',
            href: '/enrollment',
            icon: UserPlusIcon,
          },
          {
            id: 'verification',
            label: 'Verificación',
            href: '/verification',
            icon: Shield,
          },
        ]
      : [
          // Admin navigation
          {
            id: 'admin-dashboard',
            label: 'Dashboard',
            href: '/admin/dashboard',
            icon: Home,
          },
          {
            id: 'users',
            label: 'Usuarios',
            href: '/admin/users',
            icon: Users,
          },
          {
            id: 'phrases',
            label: 'Frases',
            href: '/admin/phrases',
            icon: Mic,
          },
          {
            id: 'logs',
            label: 'Logs',
            href: '/admin/logs',
            icon: Settings,
          },
          {
            id: 'phrase-rules',
            label: 'Reglas de Calidad',
            href: '/admin/phrase-rules',
            icon: Settings,
          },
        ];

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-64 backdrop-blur-xl bg-white dark:bg-gray-900/70 border-r border-blue-200/40 dark:border-gray-600/40 shadow-xl">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center px-6 py-4 border-b border-blue-200/30 dark:border-gray-600/30">
          <div className="h-12 w-12 bg-linear-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
            <Mic className="h-7 w-7 text-white" aria-hidden="true" />
          </div>
          <h1 className="ml-3 text-xl font-bold bg-linear-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent">
            VoiceAuth
          </h1>
        </div>

        {/* User Profile Link */}
        <div className="px-4 py-3 border-b border-blue-200/30 dark:border-gray-600/30">
          <Link
            to="/profile"
            className="flex items-center hover:opacity-80 transition-opacity group"
            aria-label={`Ver perfil de ${user?.fullName || user?.username}`}
          >
            <div className="h-12 w-12 bg-linear-to-br from-blue-100 to-indigo-100 dark:from-gray-700 dark:to-gray-600 rounded-xl flex items-center justify-center shadow-sm border border-blue-200/40 dark:border-gray-600/40 group-hover:border-blue-400 dark:group-hover:border-blue-500 transition-colors">
              <span className="text-lg font-bold bg-linear-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
                {user?.fullName
                  ? user.fullName
                      .split(' ')
                      .map((n) => n[0])
                      .join('')
                      .toUpperCase()
                      .slice(0, 2)
                  : user?.username?.slice(0, 2).toUpperCase() || 'U'}
              </span>
            </div>
            <div className="ml-3 flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate">
                {user?.fullName || user?.username}
              </p>
              <p className="text-xs text-gray-700 dark:text-gray-300 truncate">{user?.email}</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav
          className="flex-1 px-4 py-6 space-y-2"
          role="navigation"
          aria-label="Navegación principal"
        >
          {navigation.map((item) => {
            const IconComponent = item.icon;
            const isActive = location.pathname === item.href;

            return (
              <Link
                key={item.id}
                to={item.href}
                className={`flex items-center px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                  isActive
                    ? 'bg-linear-to-r from-blue-500 to-indigo-600 text-white shadow-lg backdrop-blur-sm border border-blue-300/50'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-white dark:bg-gray-900/60 dark:hover:bg-gray-700/60 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-sm backdrop-blur-sm border border-transparent hover:border-blue-200/30 dark:hover:border-blue-500/30'
                }`}
                aria-label={item.label}
                aria-current={isActive ? 'page' : undefined}
              >
                <IconComponent className="h-5 w-5 mr-3" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-blue-200/30 dark:border-gray-600/30 space-y-2">
          <Link
            to="/settings"
            className="flex items-center px-4 py-3 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:bg-gray-900/60 dark:hover:bg-gray-700/60 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-300 backdrop-blur-sm border border-transparent hover:border-blue-200/30 dark:hover:border-blue-500/30"
            aria-label="Configuración de la aplicación"
          >
            <Settings className="h-5 w-5 mr-3" aria-hidden="true" />
            Configuración
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-300 backdrop-blur-sm border border-transparent hover:border-red-200/30 dark:hover:border-red-500/30"
            aria-label="Cerrar sesión"
          >
            <LogOut className="h-5 w-5 mr-3" aria-hidden="true" />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
