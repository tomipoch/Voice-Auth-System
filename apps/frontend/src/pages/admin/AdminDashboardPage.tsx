import {
  Users,
  Activity,
  Shield,
  Mic,
  AlertTriangle,
  FileText,
  CheckCircle,
  Settings,
  Bell,
  XCircle,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import adminService, {
  type SystemStats,
  type AlertNotification,
} from '../../services/adminService';
import toast from 'react-hot-toast';

const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState<AlertNotification[]>([]);

  useEffect(() => {
    fetchStats();
    fetchNotifications();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await adminService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifications = async () => {
    try {
      const data = await adminService.getNotifications(5);
      setNotifications(data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const getDayName = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('es-ES', { weekday: 'short' });
  };

  // Prepare chart data from API stats or fallback to empty
  const chartData =
    stats?.daily_verifications?.map((item) => ({
      day: getDayName(item.date),
      value: item.count,
      fullDate: item.date,
    })) || [];

  // If no data yet (e.g. loading or empty system), show placeholders for last 7 days
  const displayData =
    chartData.length > 0
      ? chartData
      : [...Array(7)].map(() => ({
          day: '',
          value: 0,
          fullDate: '',
        }));

  /*
   * Helper to render a consistent KPI card matching PhraseStatsCards style
   */
  const renderStatCard = (
    title: string,
    value: string | number,
    subtext: string,
    Icon: React.ComponentType<{ className?: string }>,
    colorClasses: { bg: string; text: string }
  ) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4 transition-all hover:shadow-md">
      <div className="flex items-center gap-4">
        <div className={`p-3 rounded-lg shrink-0 ${colorClasses.bg} ${colorClasses.text}`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            {title}
          </p>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mt-0.5">{value}</h3>
          <p className="text-xs text-gray-500 mt-1">{subtext}</p>
        </div>
      </div>
    </div>
  );

  return (
    <MainLayout>
      {/* Header matching PhrasesPage style */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Dashboard de Administración
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Resumen general y métricas del sistema
        </p>
      </div>

      <div className="space-y-6">
        {/* KPIs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {loading ? (
            // Loading Skeletons
            [...Array(4)].map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm p-4 animate-pulse border border-gray-100 dark:border-gray-700 h-24"
              ></div>
            ))
          ) : (
            <>
              {renderStatCard(
                'Total Usuarios',
                stats?.total_users?.toLocaleString() ?? '0',
                `${stats?.active_users_24h ?? 0} activos hoy`,
                Users,
                { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400' }
              )}
              {renderStatCard(
                'Tasa de Éxito',
                `${((stats?.success_rate ?? 0) * 100).toFixed(1)}%`,
                'Verificaciones exitosas',
                Shield,
                {
                  bg: 'bg-green-50 dark:bg-green-900/20',
                  text: 'text-green-600 dark:text-green-400',
                }
              )}
              {renderStatCard(
                'Verificaciones',
                stats?.total_verifications?.toLocaleString() ?? '0',
                'Total histórico',
                Mic,
                {
                  bg: 'bg-purple-50 dark:bg-purple-900/20',
                  text: 'text-purple-600 dark:text-purple-400',
                }
              )}
              {renderStatCard(
                'Fallos (24h)',
                stats?.failed_verifications_24h ?? 0,
                'Requieren revisión',
                AlertTriangle,
                {
                  bg: 'bg-orange-50 dark:bg-orange-900/20',
                  text: 'text-orange-600 dark:text-orange-400',
                }
              )}
            </>
          )}
        </div>

        {/* Charts & Links Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Charts Section */}
          <Card className="lg:col-span-2 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Tendencia de Verificaciones
              </h3>
              <div className="p-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Activity className="h-4 w-4 text-gray-500" />
              </div>
            </div>

            <div className="h-64 flex items-end justify-between gap-2">
              {displayData.map((item, index) => {
                // Calculate height in pixels (max height is 240px, leaving room for labels)
                const maxHeight = 240;
                const maxValue = Math.max(...displayData.map((d) => d.value || 0));
                const heightPx =
                  maxValue > 0 ? Math.max((item.value / maxValue) * maxHeight, 4) : 4;

                return (
                  <div key={index} className="flex flex-col items-center w-full group">
                    <div className="relative w-full flex justify-center items-end">
                      <div
                        className="w-full max-w-[32px] bg-blue-500 dark:bg-blue-600 rounded-t-md transition-all duration-300 hover:bg-blue-600 dark:hover:bg-blue-500"
                        style={{ height: `${heightPx}px` }}
                        title={`${item.value} verificaciones el ${item.fullDate}`}
                      ></div>
                    </div>
                    <span className="text-xs text-gray-500 mt-2 font-medium h-4">{item.day}</span>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Quick Actions */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                Accesos Rápidos
              </h3>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/admin/users')}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30">
                      <Users className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      Gestionar Usuarios
                    </span>
                  </div>
                </button>

                <button
                  onClick={() => navigate('/admin/logs')}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900/30">
                      <FileText className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      Logs de Auditoría
                    </span>
                  </div>
                </button>

                <button
                  onClick={() => navigate('/admin/phrase-rules')}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-orange-600 dark:text-orange-400 group-hover:bg-orange-100 dark:group-hover:bg-orange-900/30">
                      <CheckCircle className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      Reglas de Calidad
                    </span>
                  </div>
                </button>
              </div>
            </Card>

            {/* Notifications Panel */}
            <Card className="p-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
                <Bell className="h-5 w-5 text-orange-500" />
                Alertas
                {notifications.length > 0 && (
                  <span className="bg-orange-500 text-white text-xs px-2 py-0.5 rounded-full">
                    {notifications.length}
                  </span>
                )}
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {notifications.length === 0 ? (
                  <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                    Sin alertas recientes
                  </p>
                ) : (
                  notifications.map((notif) => (
                    <div
                      key={notif.id}
                      className={`p-3 rounded-lg text-sm ${
                        notif.type === 'error'
                          ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                          : notif.type === 'warning'
                            ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400'
                            : 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {notif.type === 'error' ? (
                          <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                        ) : (
                          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                        )}
                        <div>
                          <p className="font-medium">{notif.title}</p>
                          <p className="text-xs opacity-80">{notif.message}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </Card>

            {/* System Status */}
            <Card className="p-6 bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700">
              <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-gray-900 dark:text-gray-100">
                <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" /> Estado del Sistema
              </h3>
              <div className="space-y-3 mt-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">API Status</span>
                  <span className="flex items-center text-green-600 dark:text-green-400 font-medium">
                    <span className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                    Operational
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Database</span>
                  <span className="flex items-center text-green-600 dark:text-green-400 font-medium">
                    <span className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                    Operational
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default AdminDashboardPage;
