import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Mic, Shield, Users, LogOut, Settings, Home, UserPlus as UserPlusIcon, Menu, X, ChevronDown } from 'lucide-react';
import { useAuth } from '../../hooks/useAuth';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const closeMenu = () => setIsOpen(false);

  // Navigation items based on user role
  const navigation =
    user?.role === 'user'
      ? [
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
    <>
      {/* Mobile Header - Only visible on mobile */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl border-b border-blue-200/40 dark:border-gray-600/40 shadow-lg">
        <div className="flex items-center justify-between h-16 px-4">
          {/* Logo */}
          <div className="flex items-center">
            <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg ring-2 ring-blue-400/20">
              <Mic className="h-6 w-6 text-white" aria-hidden="true" />
            </div>
            <h1 className="ml-2 text-lg font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent">
              VoiceAuth
            </h1>
          </div>

          {/* Right side buttons */}
          <div className="flex items-center gap-2">
            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="p-2 rounded-xl text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              aria-label="Cerrar sesión"
            >
              <LogOut className="h-5 w-5" />
            </button>

            {/* Hamburger Button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-xl hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors"
              aria-label={isOpen ? 'Cerrar menú' : 'Abrir menú'}
            >
              {isOpen ? (
                <X className="h-6 w-6 text-gray-700 dark:text-gray-300" />
              ) : (
                <Menu className="h-6 w-6 text-gray-700 dark:text-gray-300" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        <div
          className={`
            overflow-hidden transition-all duration-300 ease-in-out
            ${isOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0'}
          `}
        >
          <div className="border-t border-blue-200/30 dark:border-gray-600/30 bg-white dark:bg-gray-900 shadow-xl">
            {/* User Profile */}
            <Link
              to="/profile"
              onClick={closeMenu}
              className="flex items-center px-4 py-3 hover:bg-blue-50 dark:hover:bg-gray-800 transition-colors border-b border-blue-200/20 dark:border-gray-700/20"
              aria-label={`Ver perfil de ${user?.fullName || user?.username}`}
            >
              <div className="h-10 w-10 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-gray-700 dark:to-gray-600 rounded-lg flex items-center justify-center shadow-sm border border-blue-200/40 dark:border-gray-600/40">
                <span className="text-sm font-bold bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
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
              <div className="ml-3 flex-1">
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">{user?.fullName || user?.username}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400">{user?.email}</p>
              </div>
            </Link>

            {/* Navigation Links */}
            <nav className="py-2">
              {navigation.map((item) => {
                const IconComponent = item.icon;
                const isActive = location.pathname === item.href;

                return (
                  <Link
                    key={item.id}
                    to={item.href}
                    onClick={closeMenu}
                    className={`flex items-center px-4 py-3 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-50 dark:bg-gray-800 text-blue-600 dark:text-blue-400 border-l-4 border-blue-600'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-400'
                    }`}
                    aria-current={isActive ? 'page' : undefined}
                  >
                    <IconComponent className="h-5 w-5 mr-3 shrink-0" aria-hidden="true" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Settings Link */}
            <div className="border-t border-blue-200/20 dark:border-gray-700/20 py-2">
              <Link
                to="/settings"
                onClick={closeMenu}
                className="flex items-center px-4 py-3 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-800 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                <Settings className="h-5 w-5 mr-3 shrink-0" aria-hidden="true" />
                <span>Configuración</span>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Desktop Sidebar */}
      <div className="hidden lg:block fixed inset-y-0 left-0 z-50 w-64 backdrop-blur-xl bg-white/95 dark:bg-gray-900/95 border-r border-blue-200/40 dark:border-gray-600/40 shadow-2xl">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-4 border-b border-blue-200/30 dark:border-gray-600/30">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg ring-2 ring-blue-400/20">
              <Mic className="h-7 w-7 text-white" aria-hidden="true" />
            </div>
            <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent">
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
              <div className="h-12 w-12 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-gray-700 dark:to-gray-600 rounded-xl flex items-center justify-center shadow-sm border border-blue-200/40 dark:border-gray-600/40 group-hover:border-blue-400 dark:group-hover:border-blue-500 transition-colors">
                <span className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
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
                <p className="text-xs text-gray-600 dark:text-gray-400 truncate">{user?.email}</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav
            className="flex-1 px-4 py-6 space-y-2 overflow-y-auto"
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
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg ring-2 ring-blue-400/30'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-800/60 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-sm border border-transparent hover:border-blue-200/30 dark:hover:border-blue-500/30'
                  }`}
                  aria-label={item.label}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <IconComponent className="h-5 w-5 mr-3 shrink-0" aria-hidden="true" />
                  <span className="truncate">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-blue-200/30 dark:border-gray-600/30 space-y-2">
            <Link
              to="/settings"
              className="flex items-center px-4 py-3 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-800/60 hover:text-blue-600 dark:hover:text-blue-400 transition-all duration-300 border border-transparent hover:border-blue-200/30 dark:hover:border-blue-500/30"
              aria-label="Configuración de la aplicación"
            >
              <Settings className="h-5 w-5 mr-3 shrink-0" aria-hidden="true" />
              <span className="truncate">Configuración</span>
            </Link>
            <button
              onClick={handleLogout}
              className="w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-300 border border-transparent hover:border-red-200/30 dark:hover:border-red-500/30"
              aria-label="Cerrar sesión"
            >
              <LogOut className="h-5 w-5 mr-3 shrink-0" aria-hidden="true" />
              <span className="truncate">Cerrar Sesión</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;
