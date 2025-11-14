import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Mic, 
  Shield, 
  Users, 
  LogOut, 
  Settings,
  Home,
  UserCheck,
  UserPlus as UserPlusIcon
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('home');

  const handleLogout = async () => {
    await logout();
  };

  const navigation = [
    { id: 'home', label: 'Inicio', icon: Home },
    { id: 'enrollment', label: 'Registro de Voz', icon: UserPlusIcon, href: '/enrollment' },
    { id: 'verification', label: 'Verificación', icon: UserCheck, href: '/verification' },
  ];

  // Agregar navegación de admin si el usuario es administrador
  if (user?.role === 'admin') {
    navigation.push(
      { id: 'admin', label: 'Administración', icon: Users, href: '/admin' }
    );
  }

  const stats = [
    {
      title: 'Verificaciones Hoy',
      value: '24',
      icon: Shield,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Registro de Voz',
      value: user?.voice_template ? 'Configurado' : 'Pendiente',
      icon: Mic,
      color: user?.voice_template ? 'text-green-600' : 'text-orange-600',
      bgColor: user?.voice_template ? 'bg-green-50' : 'bg-orange-50',
    },
    {
      title: 'Estado de Seguridad',
      value: 'Activo',
      icon: Shield,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/15 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/15 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/15 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Sidebar with Liquid Glass Effect */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 backdrop-blur-xl bg-white/70 border-r border-blue-200/40 shadow-xl">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-4 border-b border-blue-200/30">
            <div className="h-12 w-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-lg">
              <Mic className="h-7 w-7 text-white" />
            </div>
            <h1 className="ml-3 text-xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent">VoiceAuth</h1>
          </div>

          {/* User Info */}
          <div className="px-6 py-4 border-b border-blue-200/30">
            <div className="flex items-center">
              <div className="h-12 w-12 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl flex items-center justify-center shadow-sm border border-blue-200/40">
                <span className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-semibold text-gray-800">{user?.name}</p>
                <p className="text-xs text-blue-600/70">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const IconComponent = item.icon;
              const isActive = item.id === activeTab;
              
              if (item.href) {
                return (
                  <Link
                    key={item.id}
                    to={item.href}
                    className={`flex items-center px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                      isActive
                        ? 'bg-blue-500/20 text-blue-700 shadow-sm backdrop-blur-sm border border-blue-300/30'
                        : 'text-gray-700 hover:bg-white/60 hover:text-blue-600 hover:shadow-sm backdrop-blur-sm border border-transparent hover:border-blue-200/30'
                    }`}
                  >
                    <IconComponent className="h-5 w-5 mr-3" />
                    {item.label}
                  </Link>
                );
              }

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 ${
                    isActive
                      ? 'bg-blue-500/20 text-blue-700 shadow-sm backdrop-blur-sm border border-blue-300/30'
                      : 'text-gray-700 hover:bg-white/60 hover:text-blue-600 hover:shadow-sm backdrop-blur-sm border border-transparent hover:border-blue-200/30'
                  }`}
                >
                  <IconComponent className="h-5 w-5 mr-3" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-4 py-4 border-t border-blue-200/30 space-y-3">
            <button className="w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium text-gray-700 hover:bg-white/60 hover:text-blue-600 transition-all duration-300 hover:shadow-sm backdrop-blur-sm border border-transparent hover:border-blue-200/30">
              <Settings className="h-5 w-5 mr-3" />
              Configuración
            </button>
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center px-4 py-3 bg-gradient-to-r from-red-500 to-red-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Cerrar Sesión
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 p-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-indigo-800 bg-clip-text text-transparent">
              Bienvenido, {user?.name}
            </h1>
            <p className="text-lg text-blue-600/80 font-medium mt-2">
              Panel de control de autenticación biométrica por voz
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {stats.map((stat, index) => {
              const IconComponent = stat.icon;
              return (
                <div key={index} className="backdrop-blur-xl bg-white/60 border border-blue-200/40 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
                  <div className="flex items-center">
                    <div className="p-3 rounded-xl bg-gradient-to-br from-blue-100/80 to-indigo-100/80 shadow-sm">
                      <IconComponent className="h-6 w-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-blue-600/70">
                        {stat.title}
                      </p>
                      <p className="text-lg font-bold text-gray-800">
                        {stat.value}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Actions */}
          <div className="backdrop-blur-xl bg-white/60 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
            <div className="mb-6">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent">
                Acciones Rápidas
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {!user?.voice_template && (
                <Link to="/enrollment" className="group">
                  <div className="p-6 bg-gradient-to-br from-orange-50/80 to-yellow-50/80 backdrop-blur-sm border-2 border-orange-200/60 rounded-2xl hover:border-orange-300/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-orange-100 to-yellow-100 rounded-xl shadow-sm">
                        <UserPlusIcon className="h-8 w-8 text-orange-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-800">
                          Configurar Voz
                        </h3>
                        <p className="text-sm text-orange-700/80">
                          Registra tu perfil de voz para usar el sistema
                        </p>
                      </div>
                    </div>
                  </div>
                </Link>
              )}
              
              <Link to="/verification" className="group">
                <div className="p-6 bg-gradient-to-br from-blue-50/80 to-indigo-50/80 backdrop-blur-sm border-2 border-blue-200/60 rounded-2xl hover:border-blue-300/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                  <div className="flex items-center">
                    <div className="p-3 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl shadow-sm">
                      <UserCheck className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-semibold text-gray-800">
                        Verificar Identidad
                      </h3>
                      <p className="text-sm text-blue-700/80">
                        Autentícate usando tu voz
                      </p>
                    </div>
                  </div>
                </div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;