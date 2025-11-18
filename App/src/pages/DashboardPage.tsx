import { Link } from 'react-router-dom';
import { Activity, TrendingUp, AlertCircle, Mic, Shield, Users } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useDashboardStats } from '../hooks/useDashboardStats';
import Card from '../components/ui/Card';
import MainLayout from '../components/ui/MainLayout';

const DashboardPage = () => {
  const { user } = useAuth();
  const { stats: userStats, recentActivity, systemStats, isLoading } = useDashboardStats();

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
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          ¡Bienvenido, {user?.fullName || user?.username}!
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium mt-2">
          Panel de control de autenticación biométrica por voz
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {stats.map((stat, index) => {
          const IconComponent = stat.icon;
          return (
            <div
              key={index}
              className="backdrop-blur-xl bg-white dark:bg-gray-900/70 dark:bg-gray-800/70 border border-blue-200/40 dark:border-gray-600/40 rounded-2xl p-6 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]"
            >
              <div className="flex items-center">
                <div className="p-3 rounded-xl bg-gradient-to-br from-blue-100/80 to-indigo-100/80 dark:from-blue-900/80 dark:to-indigo-900/80 shadow-sm">
                  <IconComponent className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-blue-600/70 dark:text-blue-400/70">
                    {stat.title}
                  </p>
                  <p className="text-lg font-bold text-gray-800 dark:text-gray-200">{stat.value}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="backdrop-blur-xl bg-white dark:bg-gray-900/70 dark:bg-gray-800/70 border border-blue-200/40 dark:border-gray-600/40 rounded-2xl p-8 shadow-xl">
        <div className="mb-6">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent">
            Acciones Rápidas
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {!userStats.isVoiceEnrolled && (
            <Link to="/enrollment" className="group">
              <div className="p-6 bg-gradient-to-br from-orange-50/80 to-yellow-50/80 dark:from-orange-900/80 dark:to-yellow-900/80 backdrop-blur-sm border-2 border-orange-200/60 dark:border-orange-600/60 rounded-2xl hover:border-orange-300/80 dark:hover:border-orange-500/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                <div className="flex items-center">
                  <div className="p-3 bg-gradient-to-br from-orange-100 to-yellow-100 dark:from-orange-800 dark:to-yellow-800 rounded-xl shadow-sm">
                    <Mic className="h-8 w-8 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                      Configurar Perfil de Voz
                    </h3>
                    <p className="text-sm text-orange-700/80 dark:text-orange-400/80">
                      Registra tu voz para usar el sistema de verificación
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          )}

          <Link to="/verification" className="group">
            <div
              className={`p-6 bg-gradient-to-br backdrop-blur-sm border-2 rounded-2xl transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02] ${
                userStats.isVoiceEnrolled
                  ? 'from-blue-50/80 to-indigo-50/80 dark:from-blue-900/80 dark:to-indigo-900/80 border-blue-200/60 dark:border-blue-600/60 hover:border-blue-300/80 dark:hover:border-blue-500/80'
                  : 'from-gray-50/80 to-gray-100/80 dark:from-gray-800/80 dark:to-gray-700/80 border-gray-200 dark:border-gray-700/60 dark:border-gray-600/60 hover:border-gray-300/80 dark:hover:border-gray-500/80 opacity-75'
              }`}
            >
              <div className="flex items-center">
                <div
                  className={`p-3 bg-gradient-to-br rounded-xl shadow-sm ${
                    userStats.isVoiceEnrolled
                      ? 'from-blue-100 to-indigo-100 dark:from-blue-800 dark:to-indigo-800'
                      : 'from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600'
                  }`}
                >
                  <Shield
                    className={`h-8 w-8 ${
                      userStats.isVoiceEnrolled
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-500 dark:text-gray-400 dark:text-gray-400'
                    }`}
                  />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                    Verificar Identidad
                  </h3>
                  <p
                    className={`text-sm ${
                      userStats.isVoiceEnrolled
                        ? 'text-blue-700/80 dark:text-blue-400/80'
                        : 'text-gray-500 dark:text-gray-400 dark:text-gray-400'
                    }`}
                  >
                    {userStats.isVoiceEnrolled
                      ? 'Autentícate usando tu voz'
                      : 'Requiere perfil de voz configurado'}
                  </p>
                </div>
              </div>
            </div>
          </Link>

          {user?.role === 'admin' && (
            <Link to="/admin" className="group">
              <div className="p-6 bg-gradient-to-br from-purple-50/80 to-indigo-50/80 dark:from-purple-900/80 dark:to-indigo-900/80 backdrop-blur-sm border-2 border-purple-200/60 dark:border-purple-600/60 rounded-2xl hover:border-purple-300/80 dark:hover:border-purple-500/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                <div className="flex items-center">
                  <div className="p-3 bg-gradient-to-br from-purple-100 to-indigo-100 dark:from-purple-800 dark:to-indigo-800 rounded-xl shadow-sm">
                    <Users className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                      Panel de Administración
                    </h3>
                    <p className="text-sm text-purple-700/80 dark:text-purple-400/80">
                      Gestiona usuarios y configuraciones del sistema
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      {recentActivity && recentActivity.length > 0 && (
        <div className="mt-8">
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <Activity className="h-6 w-6 mr-3 text-blue-600 dark:text-blue-400" />
                {user?.role === 'admin' ? 'Actividad del Sistema' : 'Tu Actividad Reciente'}
              </h2>
              <div className="space-y-3">
                {recentActivity.map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 dark:bg-gray-700 rounded-lg"
                  >
                    <div className="flex items-center">
                      <div
                        className={`w-3 h-3 rounded-full mr-3 ${
                          activity.type === 'success'
                            ? 'bg-green-500'
                            : activity.type === 'warning'
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                        }`}
                      ></div>
                      <div>
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                          {activity.message}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-400">
                      {activity.timestamp}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* System Metrics (only for admins) */}
      {systemStats && user?.role === 'admin' && (
        <div className="mt-8">
          <Card>
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-4">
                Métricas del Sistema
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">
                    Tiempo de Respuesta Promedio
                  </p>
                  <span className="text-sm text-blue-600 dark:text-blue-400 font-medium">
                    {systemStats.avgResponseTime || 0}ms
                  </span>
                </div>
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-sm text-green-600 dark:text-green-400 font-medium">
                    Uptime del Sistema
                  </p>
                  <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                    {systemStats.systemUptime || 0}%
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Alert for voice enrollment */}
      {!userStats.isVoiceEnrolled && (
        <div className="mt-8">
          <div className="backdrop-blur-xl bg-gradient-to-r from-orange-50/80 to-yellow-50/80 dark:from-orange-900/80 dark:to-yellow-900/80 border-2 border-orange-200/60 dark:border-orange-600/60 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-gradient-to-br from-orange-100 to-yellow-100 dark:from-orange-800 dark:to-yellow-800 rounded-xl shadow-sm">
                <AlertCircle className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-orange-900 dark:text-orange-100">
                  ¡Configura tu perfil de voz!
                </h3>
                <p className="text-orange-700 dark:text-orange-300">
                  Para aprovechar al máximo el sistema de autenticación biométrica, necesitas
                  registrar tu perfil de voz. Es un proceso rápido y seguro.
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
    </MainLayout>
  );
};

export default DashboardPage;
