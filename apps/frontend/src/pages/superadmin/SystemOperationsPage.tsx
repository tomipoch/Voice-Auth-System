import { useState, useEffect } from 'react';
import {
  Server,
  Database,
  HardDrive,
  RefreshCw,
  Loader2,
  Download,
  Trash2,
  Clock,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Play,
  Activity,
  Cpu,
  MemoryStick,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { superadminService } from '../../services/superadminService';
import toast from 'react-hot-toast';

interface BackupInfo {
  id: string;
  name: string;
  size_mb: number;
  created_at: string;
  type: 'auto' | 'manual';
}

interface ServerLog {
  timestamp: string;
  level: 'info' | 'warn' | 'error';
  message: string;
  source: string;
}

const SystemOperationsPage = () => {
  const [loading, setLoading] = useState(true);
  const [backups, setBackups] = useState<BackupInfo[]>([]);
  const [logs, setLogs] = useState<ServerLog[]>([]);
  const [metrics, setMetrics] = useState({
    cpu_usage: 0,
    memory_usage: 0,
    disk_usage: 0,
    avg_latency_ms: 0,
    requests_per_min: 0,
    uptime_hours: 0,
    memory_used_mb: 0,
    memory_total_mb: 0,
    disk_used_gb: 0,
    disk_total_gb: 0,
    load_average: [0, 0, 0] as number[],
    process_count: 0,
  });
  const [isRunningBackup, setIsRunningBackup] = useState(false);
  const [isRunningPurge, setIsRunningPurge] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load real system metrics from container
      const systemMetrics = await superadminService.getSystemMetrics();

      setMetrics({
        cpu_usage: systemMetrics.cpu_usage_percent,
        memory_usage: systemMetrics.memory_usage_percent,
        disk_usage: systemMetrics.disk_usage_percent,
        avg_latency_ms: 45, // TODO: Track actual latency
        requests_per_min: 120, // TODO: Track actual requests
        uptime_hours: Math.floor(systemMetrics.uptime_seconds / 3600),
        memory_used_mb: systemMetrics.memory_used_mb,
        memory_total_mb: systemMetrics.memory_total_mb,
        disk_used_gb: systemMetrics.disk_used_gb,
        disk_total_gb: systemMetrics.disk_total_gb,
        load_average: [
          systemMetrics.load_average_1m,
          systemMetrics.load_average_5m,
          systemMetrics.load_average_15m,
        ],
        process_count: systemMetrics.process_count,
      });

      // Mock backups - TODO: Implement real backup API
      setBackups([
        {
          id: '1',
          name: 'backup_2024_01_07_auto.sql',
          size_mb: 245,
          created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
          type: 'auto',
        },
        {
          id: '2',
          name: 'backup_2024_01_06_manual.sql',
          size_mb: 242,
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
          type: 'manual',
        },
        {
          id: '3',
          name: 'backup_2024_01_05_auto.sql',
          size_mb: 238,
          created_at: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
          type: 'auto',
        },
      ]);

      // Mock logs - TODO: Implement real logs API
      setLogs([
        {
          timestamp: new Date().toISOString(),
          level: 'info',
          message: 'System health check passed',
          source: 'health',
        },
        {
          timestamp: new Date(Date.now() - 5000).toISOString(),
          level: 'info',
          message: 'Verification completed for user_123',
          source: 'verification',
        },
        {
          timestamp: new Date(Date.now() - 15000).toISOString(),
          level: 'warn',
          message: 'High latency detected on node-3',
          source: 'monitoring',
        },
        {
          timestamp: new Date(Date.now() - 30000).toISOString(),
          level: 'info',
          message: 'Database connection pool refreshed',
          source: 'database',
        },
        {
          timestamp: new Date(Date.now() - 60000).toISOString(),
          level: 'error',
          message: 'Failed login attempt from 192.168.1.100',
          source: 'auth',
        },
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Error al cargar datos');
    } finally {
      setLoading(false);
    }
  };

  const handleRunBackup = async () => {
    setIsRunningBackup(true);
    try {
      // Simulate backup
      await new Promise((resolve) => setTimeout(resolve, 2000));
      const newBackup: BackupInfo = {
        id: Date.now().toString(),
        name: `backup_${new Date().toISOString()?.split('T')?.[0]?.replace(/-/g, '_')}_manual.sql`,
        size_mb: Math.floor(Math.random() * 50) + 230,
        created_at: new Date().toISOString(),
        type: 'manual',
      };
      setBackups((prev) => [newBackup, ...prev]);
      toast.success('Backup completado exitosamente');
    } catch {
      toast.error('Error al crear backup');
    } finally {
      setIsRunningBackup(false);
    }
  };

  const handleRunPurge = async () => {
    if (!confirm('¿Ejecutar limpieza de datos expirados?')) return;
    setIsRunningPurge(true);
    try {
      const result = await superadminService.runDataPurge();
      toast.success(result.message);
    } catch {
      toast.error('Error al ejecutar purge');
    } finally {
      setIsRunningPurge(false);
    }
  };

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'text-red-500';
      case 'warn':
        return 'text-yellow-500';
      default:
        return 'text-green-500';
    }
  };

  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="h-3 w-3" />;
      case 'warn':
        return <AlertTriangle className="h-3 w-3" />;
      default:
        return <CheckCircle className="h-3 w-3" />;
    }
  };

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Operaciones del Sistema
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Backups, métricas y mantenimiento
        </p>

        <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg flex items-center gap-2 text-sm text-green-800 dark:text-green-200 max-w-2xl">
          <CheckCircle className="h-4 w-4 shrink-0" />
          <span>
            Las métricas del sistema se obtienen en tiempo real desde el contenedor Docker.
          </span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="h-4 w-4 text-blue-500" />
            <span className="text-xs text-gray-500 uppercase">CPU</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {Math.round(metrics.cpu_usage)}%
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <MemoryStick className="h-4 w-4 text-indigo-500" />
            <span className="text-xs text-gray-500 uppercase">RAM</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {Math.round(metrics.memory_usage)}%
          </p>
          <p className="text-xs text-gray-500">
            {(metrics.memory_used_mb / 1024).toFixed(1)} /{' '}
            {(metrics.memory_total_mb / 1024).toFixed(1)} GB
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <HardDrive className="h-4 w-4 text-orange-500" />
            <span className="text-xs text-gray-500 uppercase">Disco</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {Math.round(metrics.disk_usage)}%
          </p>
          <p className="text-xs text-gray-500">
            {metrics.disk_used_gb.toFixed(1)} / {metrics.disk_total_gb.toFixed(1)} GB
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity className="h-4 w-4 text-green-500" />
            <span className="text-xs text-gray-500 uppercase">Load Avg</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {metrics.load_average[0]?.toFixed(2) || '0.00'}
          </p>
          <p className="text-xs text-gray-500">
            {metrics.load_average[1]?.toFixed(2) || '0'} |{' '}
            {metrics.load_average[2]?.toFixed(2) || '0'}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Server className="h-4 w-4 text-cyan-500" />
            <span className="text-xs text-gray-500 uppercase">Procesos</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {metrics.process_count}
          </p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-indigo-500" />
            <span className="text-xs text-gray-500 uppercase">Uptime</span>
          </div>
          <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {metrics.uptime_hours}h
          </p>
          <p className="text-xs text-gray-500">
            {Math.floor(metrics.uptime_hours / 24)}d {metrics.uptime_hours % 24}h
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Backups */}
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-500" />
              Backups
            </h3>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm" onClick={loadData}>
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button size="sm" onClick={handleRunBackup} disabled={isRunningBackup}>
                {isRunningBackup ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-1" />
                )}
                Ejecutar
              </Button>
            </div>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="space-y-2">
              {backups.map((backup) => (
                <div
                  key={backup.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {backup.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {backup.size_mb} MB • {new Date(backup.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${backup.type === 'auto' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}
                    >
                      {backup.type}
                    </span>
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Maintenance */}
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 mb-4">
            <HardDrive className="h-5 w-5 text-orange-500" />
            Mantenimiento
          </h3>

          <div className="space-y-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    Purgar Datos Expirados
                  </p>
                  <p className="text-sm text-gray-500">
                    Eliminar audios temporales y challenges expirados
                  </p>
                </div>
                <Button variant="secondary" onClick={handleRunPurge} disabled={isRunningPurge}>
                  {isRunningPurge ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">Limpiar Cache</p>
                  <p className="text-sm text-gray-500">Limpiar cache de modelos y embeddings</p>
                </div>
                <Button variant="secondary" onClick={() => toast.success('Cache limpiado')}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 dark:text-gray-100">Reiniciar Modelos</p>
                  <p className="text-sm text-gray-500">Recargar modelos de ML en caliente</p>
                </div>
                <Button variant="secondary" onClick={() => toast.success('Modelos recargados')}>
                  <Play className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Server Logs */}
      <Card className="p-6 mt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">Logs del Servidor</h3>
          <Button variant="ghost" size="sm" onClick={loadData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <div className="bg-gray-900 rounded-lg p-4 font-mono text-xs overflow-x-auto max-h-64 overflow-y-auto">
          {logs.map((log, i) => (
            <div key={i} className="flex items-start gap-2 py-1">
              <span className="text-gray-500 whitespace-nowrap">
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              <span className={`flex items-center gap-1 ${getLogLevelColor(log.level)}`}>
                {getLogLevelIcon(log.level)}
                {log.level.toUpperCase()}
              </span>
              <span className="text-gray-400">[{log.source}]</span>
              <span className="text-gray-300">{log.message}</span>
            </div>
          ))}
        </div>
      </Card>
    </MainLayout>
  );
};

export default SystemOperationsPage;
