import { Users, Activity, Shield, Mic, AlertTriangle, FileText } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import adminService, { type SystemStats } from '../../services/adminService';
import toast from 'react-hot-toast';

const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
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

  // Mock data for charts/trends - TODO: Get from API
  const trends = [
    { day: 'Lun', value: 45 },
    { day: 'Mar', value: 52 },
    { day: 'Mie', value: 49 },
    { day: 'Jue', value: 63 },
    { day: 'Vie', value: 58 },
    { day: 'Sab', value: 35 },
    { day: 'Dom', value: 28 },
  ];

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Dashboard de Administración
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Resumen general del sistema
        </p>
      </div>

      <div className="space-y-6">
        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  Total Usuarios
                </p>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {loading ? '...' : (stats?.total_users?.toLocaleString() ?? '0')}
                </h3>
              </div>
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-full">
                <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <p className="text-xs text-blue-600 mt-2 flex items-center">
              <Activity className="h-3 w-3 mr-1" /> {stats?.active_users_24h ?? 0} activos hoy
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  Tasa de Éxito
                </p>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {loading ? '...' : `${((stats?.success_rate ?? 0) * 100).toFixed(1)}%`}
                </h3>
              </div>
              <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-full">
                <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <p className="text-xs text-green-600 mt-2 flex items-center">
              <Activity className="h-3 w-3 mr-1" /> Verificaciones exitosas
            </p>
          </Card>

          <Card className="p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  Verificaciones
                </p>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {loading ? '...' : (stats?.total_verifications?.toLocaleString() ?? '0')}
                </h3>
              </div>
              <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-full">
                <Mic className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
            <p className="text-xs text-blue-600 mt-2">Total histórico</p>
          </Card>

          <Card className="p-6 border-l-4 border-orange-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Fallos (24h)</p>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {loading ? '...' : (stats?.failed_verifications_24h ?? 0)}
                </h3>
              </div>
              <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-full">
                <AlertTriangle className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
            <p className="text-xs text-orange-600 mt-2">Últimas 24 horas</p>
          </Card>
        </div>

        {/* Charts & Quick Links */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 p-6">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-6">
              Tendencia de Verificaciones (Últimos 7 días)
            </h3>
            <div className="h-64 flex items-end justify-between gap-2">
              {trends.map((item, index) => (
                <div key={index} className="flex flex-col items-center w-full group">
                  <div
                    className="w-full max-w-[40px] bg-blue-500 dark:bg-blue-600 rounded-t-lg transition-all duration-300 group-hover:bg-blue-600 dark:group-hover:bg-blue-500 relative"
                    style={{ height: `${item.value}%` }}
                  >
                    <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                      {item.value}
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 mt-2">{item.day}</span>
                </div>
              ))}
            </div>
          </Card>

          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                Accesos Directos
              </h3>
              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate('/admin/users')}
                >
                  <Users className="h-4 w-4 mr-2" />
                  Gestionar Usuarios
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate('/admin/logs')}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Ver Logs de Auditoría
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => navigate('/admin/phrases')}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Gestionar Frases
                </Button>
              </div>
            </Card>

            <Card className="p-6 bg-linear-to-br from-blue-500 to-indigo-600 text-white">
              <h3 className="text-lg font-bold mb-2">Estado del Sistema</h3>
              <p className="text-blue-100 text-sm mb-4">Todos los servicios operativos</p>
              <div className="flex items-center gap-2 text-sm">
                <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>API: Online</span>
              </div>
              <div className="flex items-center gap-2 text-sm mt-1">
                <div className="h-2 w-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>Biometría: Online</span>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default AdminDashboardPage;
