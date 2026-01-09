import { useState, useEffect } from 'react';
import {
  Monitor,
  RefreshCw,
  Loader2,
  LogOut,
  Clock,
  MapPin,
  Smartphone,
  Laptop,
  Globe,
  AlertCircle,
  Users,
  CheckCircle,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import toast from 'react-hot-toast';

interface ActiveSession {
  id: string;
  user_email: string;
  user_name: string;
  company: string;
  device_type: 'desktop' | 'mobile' | 'tablet';
  browser: string;
  ip_address: string;
  location: string;
  started_at: string;
  last_activity: string;
  is_current: boolean;
}

const SessionsPage = () => {
  const [loading, setLoading] = useState(true);
  const [sessions, setSessions] = useState<ActiveSession[]>([]);
  const [filterCompany, setFilterCompany] = useState('');

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      // Mock data - solo sesiones que tienen sentido
      const mockSessions: ActiveSession[] = [
        {
          id: '1',
          user_email: 'superadmin@sistema.com',
          user_name: 'Super Admin',
          company: 'sistema',
          device_type: 'desktop',
          browser: 'Chrome 120',
          ip_address: '192.168.1.1',
          location: 'Santiago, CL',
          started_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          last_activity: new Date().toISOString(),
          is_current: true,
        },
        {
          id: '2',
          user_email: 'admin@example.com',
          user_name: 'Admin Example',
          company: 'Example Corp',
          device_type: 'desktop',
          browser: 'Firefox 121',
          ip_address: '10.0.0.50',
          location: 'Buenos Aires, AR',
          started_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          last_activity: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
          is_current: false,
        },
      ];
      setSessions(mockSessions);
    } catch (error) {
      console.error('Error loading sessions:', error);
      toast.error('Error al cargar sesiones');
    } finally {
      setLoading(false);
    }
  };

  const handleForceLogout = (session: ActiveSession) => {
    if (session.is_current) {
      toast.error('No puedes cerrar tu propia sesión desde aquí');
      return;
    }
    if (!confirm(`¿Forzar cierre de sesión para ${session.user_email}?`)) {
      return;
    }
    setSessions((prev) => prev.filter((s) => s.id !== session.id));
    toast.success('Sesión cerrada');
  };

  const handleForceLogoutAll = () => {
    if (!confirm('¿Cerrar TODAS las sesiones excepto la tuya?')) {
      return;
    }
    setSessions((prev) => prev.filter((s) => s.is_current));
    toast.success('Todas las sesiones cerradas');
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'mobile':
        return <Smartphone className="h-4 w-4" />;
      case 'tablet':
        return <Laptop className="h-4 w-4" />;
      default:
        return <Monitor className="h-4 w-4" />;
    }
  };

  const getTimeSince = (date: string) => {
    const diff = Date.now() - new Date(date).getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    if (minutes < 1) return 'Justo ahora';
    if (minutes < 60) return `Hace ${minutes}m`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `Hace ${hours}h`;
    return `Hace ${Math.floor(hours / 24)}d`;
  };

  const companies = [...new Set(sessions.map((s) => s.company))];
  const filteredSessions = filterCompany
    ? sessions.filter((s) => s.company === filterCompany)
    : sessions;

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-purple-700 to-indigo-800 dark:from-gray-200 dark:via-purple-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Sesiones Activas
        </h1>
        <p className="text-lg text-purple-600/80 dark:text-purple-400/80 font-medium">
          Monitoreo y control de sesiones de usuarios
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-600">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Sesiones Activas</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{sessions.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600">
              <Monitor className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Desktop</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {sessions.filter((s) => s.device_type === 'desktop').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-50 dark:bg-purple-900/20 text-purple-600">
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Mobile</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {sessions.filter((s) => s.device_type === 'mobile').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 text-orange-600">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Empresas</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{companies.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Actions */}
      <Card className="p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <select
            value={filterCompany}
            onChange={(e) => setFilterCompany(e.target.value)}
            className="flex-1 min-w-[200px] px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
          >
            <option value="">Todas las empresas</option>
            {companies.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <div className="flex gap-2 ml-auto">
            <Button variant="secondary" onClick={loadSessions} className="h-12">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="danger" onClick={handleForceLogoutAll} className="h-12">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Sessions List */}
      <Card className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
          </div>
        ) : (
          <div className="space-y-3">
            {filteredSessions.map((session) => (
              <div
                key={session.id}
                className={`flex items-center justify-between p-4 rounded-lg border ${
                  session.is_current
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700'
                    : 'bg-gray-50 dark:bg-gray-800/50 border-gray-100 dark:border-gray-700'
                }`}
              >
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${session.is_current ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-700'}`}>
                    {getDeviceIcon(session.device_type)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {session.user_name}
                      </p>
                      {session.is_current && (
                        <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded">
                          Tu sesión
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{session.user_email}</p>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Globe className="h-3 w-3" />
                        {session.browser}
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {session.location}
                      </span>
                      <span>{session.ip_address}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600 dark:text-gray-300">{session.company}</p>
                    <p className="text-xs text-gray-400 flex items-center justify-end gap-1">
                      <Clock className="h-3 w-3" />
                      {getTimeSince(session.last_activity)}
                    </p>
                  </div>
                  {!session.is_current && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleForceLogout(session)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <LogOut className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}

            {filteredSessions.length === 0 && (
              <p className="text-center text-gray-500 py-12">
                No hay sesiones activas
              </p>
            )}
          </div>
        )}
      </Card>
    </MainLayout>
  );
};

export default SessionsPage;
