import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mic, Shield, Users, LogOut, Settings, Home, UserPlus as UserPlusIcon } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';
import { UserRole } from '../../types/index';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navigation = [
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
  ];

  // Agregar opciones de admin si el usuario es admin o superadmin
  if (user?.role === UserRole.ADMIN || user?.role === UserRole.SUPER_ADMIN) {
    navigation.push(
      {
        id: 'admin',
        label: 'Administración',
        href: '/admin',
        icon: Settings,
      },
      {
        id: 'users',
        label: 'Usuarios',
        href: '/admin/users',
        icon: Users,
      }
    );
  }

  return (
    <div className="fixed inset-y-0 left-0 z-50 w-64 backdrop-blur-xl bg-white dark:bg-gray-900/70 dark:bg-gray-900/70 border-r border-blue-200/40 dark:border-gray-600/40 shadow-xl">
      <div className="flex flex-col h-full">
        {/* Logo */}
        <div className="flex items-center px-6 py-4 border-b border-blue-200/30 dark:border-gray-600/30">
          <div className="h-12 w-12 bg-linear-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
            <Mic className="h-7 w-7 text-white" />
          </div>
          <h1 className="ml-3 text-xl font-bold bg-linear-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent">
            VoiceAuth
          </h1>
        </div>

        {/* User Info */}
        <div className="px-6 py-4 border-b border-blue-200/30 dark:border-gray-600/30">
          <Link to="/profile" className="flex items-center hover:opacity-80 transition-opacity group">
            <div className="h-12 w-12 bg-linear-to-br from-blue-100 to-indigo-100 dark:from-gray-700 dark:to-gray-600 rounded-xl flex items-center justify-center shadow-sm border border-blue-200/40 dark:border-gray-600/40 group-hover:border-blue-400 dark:group-hover:border-blue-500 transition-colors">
              <span className="text-lg font-bold bg-linear-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
                {user?.fullName?.charAt(0)?.toUpperCase() ||
                  user?.username?.charAt(0)?.toUpperCase() ||
                  'U'}
              </span>
            </div>
            <div className="ml-3">
              <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                {user?.fullName || user?.username}
              </p>
              <p className="text-xs text-blue-600/70 dark:text-blue-400/70">{user?.email}</p>
              {user?.role && (
                <span
                  className={`inline-block text-xs px-2 py-1 rounded-md mt-1 ${
                    user.role === UserRole.SUPER_ADMIN
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : user.role === UserRole.ADMIN
                        ? 'bg-orange-100 text-orange-700 border border-orange-200'
                        : 'bg-green-100 text-green-700 border border-green-200'
                  }`}
                >
                  {user.role === UserRole.SUPER_ADMIN
                    ? 'Super Admin'
                    : user.role === UserRole.ADMIN
                      ? 'Administrador'
                      : 'Usuario'}
                </span>
              )}
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
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
              >
                <IconComponent className="h-5 w-5 mr-3" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-blue-200/30 space-y-3">
          <Link
            to="/settings"
            className="w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-white dark:bg-gray-900/60 dark:hover:bg-gray-700/60 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-300 hover:shadow-sm backdrop-blur-sm border border-transparent hover:border-blue-200/30 dark:hover:border-blue-500/30"
          >
            <Settings className="h-5 w-5 mr-3" />
            Configuración
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center px-4 py-3 bg-linear-to-r from-red-500 to-red-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
