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
  UserPlus as UserPlusIcon,
  Activity,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useDashboardStats } from '../hooks/useDashboardStats';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import Layout from '../components/ui/Layout';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const { stats: userStats, recentActivity, systemStats, isLoading } = useDashboardStats();
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
      value: isLoading ? '...' : userStats.verificationsToday.toString(),
      icon: Shield,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Registro de Voz',
      value: userStats.isVoiceEnrolled ? 'Configurado' : 'Pendiente',
      icon: Mic,
      color: userStats.isVoiceEnrolled ? 'text-green-600' : 'text-orange-600',
      bgColor: userStats.isVoiceEnrolled ? 'bg-green-50' : 'bg-orange-50',
    },
    {
      title: 'Tasa de Éxito',
      value: isLoading ? '...' : `${userStats.successRate}%`,
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/20 rounded-full blur-3xl animate-pulse delay-500"></div>
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
                {user?.company && (
                  <p className="text-xs text-indigo-500/80 font-medium">{user.company}</p>
                )}
                {user?.role && (
                  <span className={`inline-block text-xs px-2 py-1 rounded-md mt-1 ${
                    user.role === 'superadmin' 
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : user.role === 'admin'
                      ? 'bg-orange-100 text-orange-700 border border-orange-200'
                      : 'bg-green-100 text-green-700 border border-green-200'
                  }`}>
                    {user.role === 'superadmin' ? 'Super Admin' : 
                     user.role === 'admin' ? 'Administrador' : 'Usuario'}
                  </span>
                )}
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
                <div key={index} className="backdrop-blur-xl bg-white/70 border border-blue-200/40 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
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
          <div className="backdrop-blur-xl bg-white/70 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
            <div className="mb-6">
              <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent">
                Acciones Rápidas
              </h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {!userStats.isVoiceEnrolled && (
                <Link to="/enrollment" className="group">
                  <div className="p-6 bg-gradient-to-br from-orange-50/80 to-yellow-50/80 backdrop-blur-sm border-2 border-orange-200/60 rounded-2xl hover:border-orange-300/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-orange-100 to-yellow-100 rounded-xl shadow-sm">
                        <UserPlusIcon className="h-8 w-8 text-orange-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-800">
                          Configurar Perfil de Voz
                        </h3>
                        <p className="text-sm text-orange-700/80">
                          Registra tu voz para usar el sistema de verificación
                        </p>
                      </div>
                    </div>
                  </div>
                </Link>
              )}
              
              <Link to="/verification" className="group">
                <div className={`p-6 bg-gradient-to-br backdrop-blur-sm border-2 rounded-2xl transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02] ${
                  userStats.isVoiceEnrolled ? 
                  'from-blue-50/80 to-indigo-50/80 border-blue-200/60 hover:border-blue-300/80' :
                  'from-gray-50/80 to-gray-100/80 border-gray-200/60 hover:border-gray-300/80 opacity-75'
                }`}>
                  <div className="flex items-center">
                    <div className={`p-3 bg-gradient-to-br rounded-xl shadow-sm ${
                      userStats.isVoiceEnrolled ?
                      'from-blue-100 to-indigo-100' :
                      'from-gray-100 to-gray-200'
                    }`}>
                      <UserCheck className={`h-8 w-8 ${
                        userStats.isVoiceEnrolled ? 'text-blue-600' : 'text-gray-500'
                      }`} />
                    </div>
                    <div className="ml-4">
                      <h3 className="text-lg font-semibold text-gray-800">
                        Verificar Identidad
                      </h3>
                      <p className={`text-sm ${
                        userStats.isVoiceEnrolled ? 'text-blue-700/80' : 'text-gray-500'
                      }`}>
                        {userStats.isVoiceEnrolled ? 
                          'Autentícate usando tu voz' : 
                          'Requiere perfil de voz configurado'
                        }
                      </p>
                    </div>
                  </div>
                </div>
              </Link>

              {user?.role === 'admin' && (
                <Link to="/admin" className="group">
                  <div className="p-6 bg-gradient-to-br from-purple-50/80 to-indigo-50/80 backdrop-blur-sm border-2 border-purple-200/60 rounded-2xl hover:border-purple-300/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                    <div className="flex items-center">
                      <div className="p-3 bg-gradient-to-br from-purple-100 to-indigo-100 rounded-xl shadow-sm">
                        <Settings className="h-8 w-8 text-purple-600" />
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-semibold text-gray-800">
                          Panel de Administración
                        </h3>
                        <p className="text-sm text-purple-700/80">
                          Gestionar usuarios y configuración del sistema
                        </p>
                      </div>
                    </div>
                  </div>
                </Link>
              )}
            </div>
          </div>

          {/* Información del sistema y actividad reciente */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
            {/* Estado del sistema */}
            <div className="backdrop-blur-xl bg-white/70 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-6 flex items-center gap-3">
                <div className="h-8 w-8 bg-gradient-to-br from-green-400/20 to-green-600/20 rounded-xl flex items-center justify-center">
                  <Activity className="h-5 w-5 text-green-600" />
                </div>
                Estado del Sistema
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-white/50 backdrop-blur-sm rounded-xl border border-green-200/30">
                  <span className="text-sm font-medium text-gray-700">Servidor de IA</span>
                  <span className="px-3 py-1 text-xs font-bold text-green-800 bg-gradient-to-r from-green-100 to-green-200 rounded-full shadow-sm">
                    🟢 Activo
                  </span>
                </div>
                <div className="flex items-center justify-between p-3 bg-white/50 backdrop-blur-sm rounded-xl border border-green-200/30">
                  <span className="text-sm font-medium text-gray-700">Base de Datos</span>
                  <span className="px-3 py-1 text-xs font-bold text-green-800 bg-gradient-to-r from-green-100 to-green-200 rounded-full shadow-sm">
                    🟢 Conectado
                  </span>
                </div>
                {systemStats && (
                  <>
                    <div className="flex items-center justify-between p-3 bg-white/50 backdrop-blur-sm rounded-xl border border-blue-200/30">
                      <span className="text-sm font-medium text-gray-700">Tiempo de Respuesta</span>
                      <span className="text-sm text-blue-600 font-medium">{systemStats.avg_response_time}ms</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-white/50 backdrop-blur-sm rounded-xl border border-blue-200/30">
                      <span className="text-sm font-medium text-gray-700">Disponibilidad</span>
                      <span className="text-sm text-green-600 font-medium">{systemStats.system_uptime}%</span>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Actividad reciente */}
            <div className="backdrop-blur-xl bg-white/70 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-6 flex items-center gap-3">
                <div className="h-8 w-8 bg-gradient-to-br from-cyan-400/20 to-cyan-600/20 rounded-xl flex items-center justify-center">
                  <TrendingUp className="h-5 w-5 text-cyan-600" />
                </div>
                {user?.role === 'admin' ? 'Actividad del Sistema' : 'Tu Actividad Reciente'}
              </h3>
              <div className="space-y-3">
                {recentActivity.length > 0 ? (
                  recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-center space-x-4 p-4 bg-white/50 backdrop-blur-sm rounded-xl border border-blue-200/20 hover:bg-blue-50/50 transition-all duration-300">
                      <div className={`w-3 h-3 rounded-full ${
                        activity.type === 'success' ? 'bg-green-500' :
                        activity.type === 'error' ? 'bg-red-500' :
                        activity.type === 'warning' ? 'bg-yellow-500' :
                        'bg-blue-500'
                      }`}></div>
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-900">
                          {activity.message || activity.details}
                        </span>
                        {activity.user_name && user?.role === 'admin' && (
                          <p className="text-xs text-gray-600 mt-1">
                            Por: {activity.user_name}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-blue-600/70 font-medium">
                        {activity.timestamp}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-sm">No hay actividad reciente</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Alerta si no tiene perfil de voz configurado */}
          {!userStats.isVoiceEnrolled && (
            <div className="mt-8">
              <div className="backdrop-blur-xl bg-gradient-to-r from-yellow-50/80 to-orange-50/80 border border-yellow-200/50 rounded-2xl p-6 shadow-xl">
                <div className="flex items-center space-x-4">
                  <div className="h-12 w-12 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-2xl flex items-center justify-center">
                    <AlertCircle className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-orange-900">
                      ¡Configura tu perfil de voz!
                    </h3>
                    <p className="text-orange-700">
                      Para aprovechar al máximo el sistema de autenticación biométrica, necesitas registrar tu perfil de voz. Es un proceso rápido y seguro.
                    </p>
                  </div>
                  <Link to="/enrollment">
                    <button className="py-3 px-6 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] flex items-center gap-2">
                      <Mic className="h-4 w-4" />
                      Configurar ahora
                    </button>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;