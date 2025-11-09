import { 
  Activity, 
  Users, 
  Shield, 
  AlertTriangle, 
  TrendingUp, 
  Clock,
  CheckCircle,
  XCircle
} from 'lucide-react';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';

const SystemMetrics = ({ metrics = {}, isLoading = false }) => {
  const {
    totalUsers = 0,
    enrolledUsers = 0,
    verificationAttempts = 0,
    successfulVerifications = 0,
    failedVerifications = 0,
    systemHealth = 'unknown',
    responseTime = 0,
    uptime = 0,
    recentActivity = []
  } = metrics;

  const successRate = verificationAttempts > 0 
    ? ((successfulVerifications / verificationAttempts) * 100).toFixed(1)
    : 0;

  const enrollmentRate = totalUsers > 0 
    ? ((enrolledUsers / totalUsers) * 100).toFixed(1)
    : 0;

  const getHealthStatus = (health) => {
    switch (health) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'pending';
    }
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Métricas principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Usuarios Totales</p>
              <p className="text-2xl font-semibold text-gray-900">{totalUsers}</p>
              <p className="text-xs text-gray-500">
                {enrollmentRate}% registrados
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Shield className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Tasa de Éxito</p>
              <p className="text-2xl font-semibold text-gray-900">{successRate}%</p>
              <p className="text-xs text-gray-500">
                {successfulVerifications} / {verificationAttempts} intentos
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Activity className="h-8 w-8 text-purple-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Estado del Sistema</p>
              <div className="flex items-center space-x-2 mt-1">
                <StatusIndicator 
                  status={getHealthStatus(systemHealth)} 
                  size="sm" 
                />
                <span className="text-sm font-medium capitalize">{systemHealth}</span>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Clock className="h-8 w-8 text-orange-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Tiempo de Respuesta</p>
              <p className="text-2xl font-semibold text-gray-900">{responseTime}ms</p>
              <p className="text-xs text-gray-500">
                Uptime: {formatUptime(uptime)}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Métricas detalladas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Estadísticas de verificación */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Estadísticas de Verificación
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <span className="text-sm text-gray-600">Verificaciones Exitosas</span>
              </div>
              <span className="text-lg font-semibold text-green-600">
                {successfulVerifications}
              </span>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <XCircle className="h-5 w-5 text-red-600" />
                <span className="text-sm text-gray-600">Verificaciones Fallidas</span>
              </div>
              <span className="text-lg font-semibold text-red-600">
                {failedVerifications}
              </span>
            </div>
            
            <div className="pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-900">Tasa de Éxito</span>
                <span className="text-lg font-bold text-gray-900">{successRate}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-green-600 h-2 rounded-full" 
                  style={{ width: `${successRate}%` }}
                ></div>
              </div>
            </div>
          </div>
        </Card>

        {/* Actividad reciente */}
        <Card className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Actividad Reciente
          </h3>
          <div className="space-y-3">
            {recentActivity.length > 0 ? (
              recentActivity.slice(0, 5).map((activity, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    activity.type === 'success' ? 'bg-green-500' :
                    activity.type === 'error' ? 'bg-red-500' :
                    activity.type === 'warning' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`}></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 truncate">
                      {activity.message}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500 italic">
                No hay actividad reciente
              </p>
            )}
          </div>
        </Card>
      </div>

      {/* Alertas del sistema */}
      {systemHealth !== 'healthy' && (
        <Card className="p-6 border-yellow-200 bg-yellow-50">
          <div className="flex items-center space-x-3">
            <AlertTriangle className="h-6 w-6 text-yellow-600" />
            <div>
              <h3 className="text-lg font-medium text-yellow-900">
                Alerta del Sistema
              </h3>
              <p className="text-sm text-yellow-700">
                {systemHealth === 'warning' 
                  ? 'El sistema presenta algunos problemas menores que requieren atención.'
                  : 'El sistema presenta problemas críticos que requieren atención inmediata.'
                }
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default SystemMetrics;