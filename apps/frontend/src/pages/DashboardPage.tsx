import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Mic, Shield, Users, Activity, AlertCircle } from 'lucide-react';
import MainLayout from '../components/ui/MainLayout';
import Card from '../components/ui/Card';
import { useAuth } from '../hooks/useAuth';
import { verificationService } from '../services/apiServices';

interface ActivityItem {
  type: 'success' | 'error' | 'warning';
  message: string;
  timestamp: string;
}

interface HistoryAttempt {
  result: string;
  score: number;
  date: string;
}

const DashboardPage = () => {
  const { user } = useAuth();
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch real data from backend
  useEffect(() => {
    const fetchHistory = async () => {
      if (user?.id) {
        try {
          const response = await verificationService.getVerificationHistory(user.id, 5);
          if (response.success && response.history?.recent_attempts) {
            // Transform backend data to match activity format
            const activities = response.history.recent_attempts.map(
              (h: HistoryAttempt) =>
                ({
                  type: h.result === 'success' ? 'success' : 'error',
                  message:
                    h.result === 'success'
                      ? `Verificación exitosa (${h.score}%)`
                      : `Verificación fallida (${h.score}%)`,
                  timestamp: h.date,
                }) as ActivityItem
            );
            setRecentActivity(activities);
          }
        } catch (error) {
          console.error('Error fetching history:', error);
        } finally {
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [user]);

  const userStats = {
    isVoiceEnrolled: user?.voice_template ? true : false,
  };

  const systemStats = {
    avgResponseTime: 150,
    systemUptime: 99.9,
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-linear-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent mb-2">
          ¡Bienvenido, {user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'Usuario'}!
        </h1>
        <p className="text-lg text-gray-700 dark:text-gray-300">
          {user?.role === 'admin'
            ? 'Panel de control administrativo'
            : 'Tu panel de autenticación biométrica por voz'}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200 mb-4">
          Acciones Rápidas
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Link
            to="/enrollment"
            className={`group ${!userStats.isVoiceEnrolled ? 'animate-pulse' : ''}`}
          >
            <div
              className={`p-6 bg-linear-to-br backdrop-blur-sm border-2 rounded-2xl transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02] ${
                userStats.isVoiceEnrolled
                  ? 'from-green-50/80 to-emerald-50/80 dark:from-green-900/80 dark:to-emerald-900/80 border-green-200/60 dark:border-green-600/60 hover:border-green-300/80 dark:hover:border-green-500/80'
                  : 'from-orange-50/80 to-amber-50/80 dark:from-orange-900/80 dark:to-amber-900/80 border-orange-200/60 dark:border-orange-600/60 hover:border-orange-300/80 dark:hover:border-orange-500/80'
              }`}
            >
              <div className="flex items-center">
                <div
                  className={`p-3 bg-linear-to-br rounded-xl shadow-sm ${
                    userStats.isVoiceEnrolled
                      ? 'from-green-100 to-emerald-100 dark:from-green-800 dark:to-emerald-800'
                      : 'from-orange-100 to-amber-100 dark:from-orange-800 dark:to-amber-800'
                  }`}
                >
                  <Mic
                    className={`h-8 w-8 ${
                      userStats.isVoiceEnrolled
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-orange-600 dark:text-orange-400'
                    }`}
                  />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
                    {userStats.isVoiceEnrolled
                      ? 'Actualizar Perfil de Voz'
                      : 'Registrar Perfil de Voz'}
                  </h3>
                  <p
                    className={`text-sm ${
                      userStats.isVoiceEnrolled
                        ? 'text-green-700/80 dark:text-green-400/80'
                        : 'text-orange-700/80 dark:text-orange-400/80'
                    }`}
                  >
                    {userStats.isVoiceEnrolled
                      ? 'Mejora tu perfil biométrico'
                      : '¡Configura tu huella de voz ahora!'}
                  </p>
                </div>
              </div>
            </div>
          </Link>

          <Link
            to="/verification"
            className={`group ${!userStats.isVoiceEnrolled ? 'pointer-events-none' : ''}`}
          >
            <div
              className={`p-6 bg-linear-to-br backdrop-blur-sm border-2 rounded-2xl transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02] ${
                userStats.isVoiceEnrolled
                  ? 'from-blue-50/80 to-indigo-50/80 dark:from-blue-900/80 dark:to-indigo-900/80 border-blue-200/60 dark:border-blue-600/60 hover:border-blue-300/80 dark:hover:border-blue-500/80'
                  : 'from-gray-50/80 to-gray-100/80 dark:from-gray-800/80 dark:to-gray-700/80 border-gray-200 dark:border-gray-600/60 hover:border-gray-300/80 dark:hover:border-gray-500/80 opacity-75'
              }`}
            >
              <div className="flex items-center">
                <div
                  className={`p-3 bg-linear-to-br rounded-xl shadow-sm ${
                    userStats.isVoiceEnrolled
                      ? 'from-blue-100 to-indigo-100 dark:from-blue-800 dark:to-indigo-800'
                      : 'from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600'
                  }`}
                >
                  <Shield
                    className={`h-8 w-8 ${
                      userStats.isVoiceEnrolled
                        ? 'text-blue-600 dark:text-blue-400'
                        : 'text-gray-600 dark:text-gray-400'
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
                        : 'text-gray-600 dark:text-gray-400'
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
              <div className="p-6 bg-linear-to-br from-purple-50/80 to-indigo-50/80 dark:from-purple-900/80 dark:to-indigo-900/80 backdrop-blur-sm border-2 border-purple-200/60 dark:border-purple-600/60 rounded-2xl hover:border-purple-300/80 dark:hover:border-purple-500/80 transition-all duration-300 hover:shadow-lg group-hover:scale-[1.02]">
                <div className="flex items-center">
                  <div className="p-3 bg-linear-to-br from-purple-100 to-indigo-100 dark:from-purple-800 dark:to-indigo-800 rounded-xl shadow-sm">
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
      {!isLoading && recentActivity && recentActivity.length > 0 && (
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
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
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
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      {new Date(activity.timestamp).toLocaleString('es-CL', {
                        timeZone: 'America/Santiago',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
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
          <div className="backdrop-blur-xl bg-linear-to-r from-orange-50/80 to-yellow-50/80 dark:from-orange-900/80 dark:to-yellow-900/80 border-2 border-orange-200/60 dark:border-orange-600/60 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-linear-to-br from-orange-100 to-yellow-100 dark:from-orange-800 dark:to-yellow-800 rounded-xl shadow-sm">
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
                <button className="py-3 px-6 bg-linear-to-r from-orange-500 to-orange-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] flex items-center gap-2">
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
