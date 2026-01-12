import { useState, useEffect } from 'react';
import {
  Shield,
  RefreshCw,
  Loader2,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Activity,
  TrendingUp,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import toast from 'react-hot-toast';

interface SpoofAttempt {
  id: string;
  timestamp: string;
  user_email: string;
  company: string;
  attack_type: 'replay' | 'tts' | 'voice_clone' | 'unknown';
  confidence: number;
  blocked: boolean;
  ip_address: string;
}

const SecurityDashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [attempts, setAttempts] = useState<SpoofAttempt[]>([]);
  const [stats, setStats] = useState({
    total_attempts_24h: 0,
    blocked_24h: 0,
    detection_rate: 0,
    top_attack_type: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Mock data - in production would call API
      const mockAttempts: SpoofAttempt[] = [
        {
          id: '1',
          timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          user_email: 'test@example.com',
          company: 'Example Corp',
          attack_type: 'replay',
          confidence: 0.92,
          blocked: true,
          ip_address: '192.168.1.100',
        },
        {
          id: '2',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          user_email: 'user@familia.com',
          company: 'Familia',
          attack_type: 'tts',
          confidence: 0.87,
          blocked: true,
          ip_address: '10.0.0.50',
        },
        {
          id: '3',
          timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
          user_email: 'admin@sistema.com',
          company: 'sistema',
          attack_type: 'voice_clone',
          confidence: 0.78,
          blocked: true,
          ip_address: '172.16.0.1',
        },
      ];

      setAttempts(mockAttempts);
      setStats({
        total_attempts_24h: mockAttempts.length,
        blocked_24h: mockAttempts.filter((a) => a.blocked).length,
        detection_rate: 0.95,
        top_attack_type: 'replay',
      });
    } catch (error) {
      console.error('Error loading security data:', error);
      toast.error('Error al cargar datos de seguridad');
    } finally {
      setLoading(false);
    }
  };

  const getAttackTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      replay: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      tts: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
      voice_clone: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
      unknown: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400',
    };
    const labels: Record<string, string> = {
      replay: 'Replay Attack',
      tts: 'TTS (Síntesis)',
      voice_clone: 'Voice Clone',
      unknown: 'Desconocido',
    };
    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${colors[type]}`}
      >
        {labels[type]}
      </span>
    );
  };

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-red-700 to-orange-800 dark:from-gray-200 dark:via-red-400 dark:to-orange-400 bg-clip-text text-transparent mb-2">
          Dashboard de Seguridad
        </h1>
        <p className="text-lg text-red-600/80 dark:text-red-400/80 font-medium">
          Monitoreo de intentos de spoofing y amenazas
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Intentos (24h)</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {stats.total_attempts_24h}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-600">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Bloqueados</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {stats.blocked_24h}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Tasa Detección</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {(stats.detection_rate * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 text-orange-600">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Ataque Top</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100 capitalize">
                {stats.top_attack_type}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Attack Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Intentos Recientes de Spoofing
            </h3>
            <Button variant="secondary" size="sm" onClick={loadData}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-8 w-8 animate-spin text-red-500" />
            </div>
          ) : (
            <div className="space-y-3">
              {attempts.map((attempt) => (
                <div
                  key={attempt.id}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-100 dark:border-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded-lg ${attempt.blocked ? 'bg-green-100 dark:bg-green-900/20' : 'bg-red-100 dark:bg-red-900/20'}`}
                    >
                      {attempt.blocked ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-600" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {attempt.user_email}
                      </p>
                      <p className="text-xs text-gray-500">
                        {attempt.company} • {attempt.ip_address}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {getAttackTypeBadge(attempt.attack_type)}
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {(attempt.confidence * 100).toFixed(0)}%
                      </p>
                      <p className="text-xs text-gray-500 flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {new Date(attempt.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              {attempts.length === 0 && (
                <p className="text-center text-gray-500 py-8">
                  No hay intentos de spoofing recientes
                </p>
              )}
            </div>
          )}
        </Card>

        {/* Attack Type Distribution */}
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
            Tipos de Ataque
          </h3>
          <div className="space-y-4">
            {[
              { type: 'Replay Attack', count: 45, color: 'bg-red-500' },
              { type: 'TTS Síntesis', count: 30, color: 'bg-orange-500' },
              { type: 'Voice Clone', count: 20, color: 'bg-indigo-500' },
              { type: 'Desconocido', count: 5, color: 'bg-gray-500' },
            ].map((item) => (
              <div key={item.type}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600 dark:text-gray-300">{item.type}</span>
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {item.count}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`${item.color} h-2 rounded-full transition-all`}
                    style={{ width: `${item.count}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Alert Message */}
      <Card className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Sistema de detección activo
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-300 mt-1">
              El sistema anti-spoofing está funcionando correctamente. Todos los intentos detectados
              son bloqueados automáticamente.
            </p>
          </div>
        </div>
      </Card>
    </MainLayout>
  );
};

export default SecurityDashboardPage;
