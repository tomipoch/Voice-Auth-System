import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Users,
  Shield,
  Server,
  Database,
  Cpu,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  FileText,
  Settings,
  Trash2,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import MainLayout from '../components/ui/MainLayout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { superadminService } from '../services/superadminService';
import type {
  GlobalStats,
  CompanyStats,
  SystemHealth,
  ModelInfo,
  AuditLogEntry,
} from '../services/superadminService';
import toast from 'react-hot-toast';

const SuperAdminDashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [globalStats, setGlobalStats] = useState<GlobalStats | null>(null);
  const [companies, setCompanies] = useState<CompanyStats[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [stats, companiesData, health, modelsData, logs] = await Promise.all([
        superadminService.getGlobalStats(),
        superadminService.getCompanies(),
        superadminService.getSystemHealth(),
        superadminService.getModelsStatus(),
        superadminService.getAuditLogs({ limit: 10 }),
      ]);
      setGlobalStats(stats);
      setCompanies(companiesData);
      setSystemHealth(health);
      setModels(modelsData);
      setAuditLogs(logs);
    } catch (_err) {
      console.error('Error loading data:', _err);
      setError('Error al cargar datos. Verifica que tienes permisos de superadmin.');
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handlePurge = async () => {
    if (!confirm('¿Estás seguro de ejecutar la limpieza de datos expirados?')) {
      return;
    }

    try {
      const result = await superadminService.runDataPurge();
      toast.success(result.message);
    } catch {
      toast.error('Error al ejecutar purge');
    }
  };

  /*
   * Helper to render a consistent KPI card matching AdminDashboard style
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'loaded':
        return 'text-green-400';
      case 'degraded':
      case 'loading':
        return 'text-yellow-400';
      default:
        return 'text-red-400';
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <Card className="p-6">
          <div className="flex items-center gap-3 text-red-500 mb-4">
            <AlertCircle className="h-5 w-5" />
            <span>{error}</span>
          </div>
          <Button onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Reintentar
          </Button>
        </Card>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Header matching AdminDashboard style */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
              Panel de Super Administrador
            </h1>
            <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
              Control global del sistema y todas las empresas
            </p>
          </div>
          <Button variant="ghost" onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualizar
          </Button>
        </div>
      </div>

      <div className="space-y-6">
        {/* KPIs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {renderStatCard(
            'Total Empresas',
            globalStats?.total_companies ?? 0,
            `${companies.length} empresas activas`,
            Building2,
            { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400' }
          )}
          {renderStatCard(
            'Usuarios Globales',
            globalStats?.total_users?.toLocaleString() ?? '0',
            `${globalStats?.total_enrollments ?? 0} enrolados`,
            Users,
            {
              bg: 'bg-indigo-50 dark:bg-indigo-900/20',
              text: 'text-indigo-600 dark:text-indigo-400',
            }
          )}
          {renderStatCard(
            'Verificaciones (30d)',
            globalStats?.total_verifications_30d?.toLocaleString() ?? '0',
            `${((globalStats?.success_rate ?? 0) * 100).toFixed(1)}% éxito`,
            Shield,
            { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400' }
          )}
          {renderStatCard(
            'Spoofing Detectado',
            `${((globalStats?.spoof_detection_rate ?? 0) * 100).toFixed(2)}%`,
            'Tasa de detección',
            AlertTriangle,
            {
              bg: 'bg-orange-50 dark:bg-orange-900/20',
              text: 'text-orange-600 dark:text-orange-400',
            }
          )}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Companies Table */}
          <Card className="lg:col-span-2 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Empresas por Usuarios
              </h3>
              <div className="p-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <Building2 className="h-4 w-4 text-gray-500" />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                      Empresa
                    </th>
                    <th className="text-center py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                      Usuarios
                    </th>
                    <th className="text-center py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                      Enrolados
                    </th>
                    <th className="text-center py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                      Verif. (30d)
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {companies.slice(0, 5).map((company, index) => (
                    <tr key={index} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                            <Building2 className="h-4 w-4 text-blue-600" />
                          </div>
                          <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                            {company.name}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 text-center text-sm text-gray-600 dark:text-gray-300">
                        {company.user_count}
                      </td>
                      <td className="py-3 text-center">
                        <span className="text-sm text-green-600 dark:text-green-400 font-medium">
                          {company.enrolled_count}
                        </span>
                      </td>
                      <td className="py-3 text-center text-sm text-gray-600 dark:text-gray-300">
                        {company.verification_count_30d}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Quick Actions & System Status */}
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
                    <div className="p-2 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg text-indigo-600 dark:text-indigo-400 group-hover:bg-indigo-100 dark:group-hover:bg-indigo-900/30">
                      <FileText className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      Auditoría Global
                    </span>
                  </div>
                </button>

                <button
                  onClick={handlePurge}
                  className="w-full flex items-center justify-between p-3 rounded-lg border border-orange-200 dark:border-orange-700/50 hover:bg-orange-50 dark:hover:bg-orange-900/20 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded-lg text-orange-600 dark:text-orange-400 group-hover:bg-orange-100 dark:group-hover:bg-orange-900/30">
                      <Trash2 className="h-4 w-4" />
                    </div>
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
                      Purgar Datos Expirados
                    </span>
                  </div>
                </button>
              </div>
            </Card>

            {/* System Status Card */}
            <Card className="p-6 bg-gray-900 text-white border-none">
              <h3 className="text-lg font-bold mb-2 flex items-center gap-2">
                <Settings className="h-5 w-5" /> Estado del Sistema
              </h3>
              <div className="space-y-3 mt-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Server className="h-4 w-4" /> API
                  </span>
                  <span
                    className={`flex items-center font-medium ${getStatusColor(systemHealth?.api_status || 'down')}`}
                  >
                    <span className="h-2 w-2 bg-current rounded-full mr-2 animate-pulse"></span>
                    {systemHealth?.api_status || 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Database className="h-4 w-4" /> Database
                  </span>
                  <span
                    className={`flex items-center font-medium ${getStatusColor(systemHealth?.database_status || 'down')}`}
                  >
                    <span className="h-2 w-2 bg-current rounded-full mr-2 animate-pulse"></span>
                    {systemHealth?.database_connections}/{systemHealth?.database_max_connections}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 flex items-center gap-2">
                    <Cpu className="h-4 w-4" /> Modelos AI
                  </span>
                  <span
                    className={`flex items-center font-medium ${getStatusColor(models[0]?.status || 'not_loaded')}`}
                  >
                    <span className="h-2 w-2 bg-current rounded-full mr-2 animate-pulse"></span>
                    {models.filter((m) => m.status === 'loaded').length}/{models.length} loaded
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Recent Activity */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Actividad Reciente Global
            </h3>
            <Button variant="ghost" size="sm" onClick={() => navigate('/admin/logs')}>
              Ver todos
            </Button>
          </div>
          <div className="space-y-2">
            {auditLogs.length === 0 ? (
              <p className="text-gray-500 text-sm">No hay actividad reciente</p>
            ) : (
              auditLogs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-1.5 rounded-lg ${log.success ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}
                    >
                      {log.success ? (
                        <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {log.action}
                      </p>
                      <p className="text-xs text-gray-500">
                        {log.actor} • {log.company || 'sistema'}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};

export default SuperAdminDashboard;
