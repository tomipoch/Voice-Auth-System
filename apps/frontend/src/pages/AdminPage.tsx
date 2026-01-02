import { useState, useEffect } from 'react';
import {
  Users,
  Settings,
  Activity,
  Shield,
  Search,
  Mic,
  BarChart2,
  AlertTriangle,
  FileText,
  ChevronRight,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../components/ui/MainLayout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

interface MockUser {
  id: number;
  username: string;
  email: string;
  role: string;
  status: string;
  voiceEnrolled: boolean;
}

const AdminPage = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [users, setUsers] = useState<MockUser[]>([]);
  const [searchTerm, setSearchTerm] = useState('');

  // Mock data for charts/trends
  const trends = [
    { day: 'Lun', value: 45 },
    { day: 'Mar', value: 52 },
    { day: 'Mie', value: 49 },
    { day: 'Jue', value: 63 },
    { day: 'Vie', value: 58 },
    { day: 'Sab', value: 35 },
    { day: 'Dom', value: 28 },
  ];

  useEffect(() => {
    if (activeTab === 'users') {
      // Mock users for now
      setTimeout(() => {
        setUsers([
          {
            id: 1,
            username: 'juan.perez',
            email: 'juan.perez@example.com',
            role: 'user',
            status: 'active',
            voiceEnrolled: true,
          },
          {
            id: 2,
            username: 'maria.gomez',
            email: 'maria.gomez@example.com',
            role: 'user',
            status: 'active',
            voiceEnrolled: false,
          },
          {
            id: 3,
            username: 'carlos.ruiz',
            email: 'carlos.ruiz@example.com',
            role: 'admin',
            status: 'active',
            voiceEnrolled: true,
          },
        ]);
      }, 500);
    }
  }, [activeTab]);

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Total Usuarios</p>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">1,234</h3>
            </div>
            <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-full">
              <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <p className="text-xs text-green-600 mt-2 flex items-center">
            <Activity className="h-3 w-3 mr-1" /> +12% este mes
          </p>
        </Card>

        <Card className="p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Tasa de Éxito</p>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">98.5%</h3>
            </div>
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-full">
              <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <p className="text-xs text-green-600 mt-2 flex items-center">
            <Activity className="h-3 w-3 mr-1" /> +0.5% vs semana pasada
          </p>
        </Card>

        <Card className="p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Verificaciones</p>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">8,543</h3>
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
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Alertas</p>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">3</h3>
            </div>
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-full">
              <AlertTriangle className="h-6 w-6 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <p className="text-xs text-orange-600 mt-2">Requieren atención</p>
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
                onClick={() => setActiveTab('users')}
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
                onClick={() => setActiveTab('settings')}
              >
                <Settings className="h-4 w-4 mr-2" />
                Configuración del Sistema
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
  );

  const renderUsers = () => (
    <Card className="p-6">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Usuarios</h2>
        <div className="relative w-full md:w-64">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Buscar usuario..."
            className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Usuario
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Rol
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Estado
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Biometría
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {users.map((u) => (
              <tr
                key={u.id}
                className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                onClick={() => navigate(`/admin/users/${u.id}`)}
              >
                <td className="py-3 px-4">
                  <div className="flex items-center">
                    <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold mr-3">
                      {u.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">{u.username}</p>
                      <p className="text-xs text-gray-500">{u.email}</p>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 capitalize">
                    {u.role}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 capitalize">
                    {u.status}
                  </span>
                </td>
                <td className="py-3 px-4">
                  {u.voiceEnrolled ? (
                    <span className="flex items-center text-green-600 text-sm">
                      <Mic className="h-3 w-3 mr-1" /> Activo
                    </span>
                  ) : (
                    <span className="flex items-center text-orange-500 text-sm">
                      <AlertTriangle className="h-3 w-3 mr-1" /> Pendiente
                    </span>
                  )}
                </td>
                <td className="py-3 px-4 text-right">
                  <Button variant="ghost" size="sm">
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Panel de Administración
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Gestión de empresa y usuarios
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-xl mb-8 w-fit">
        {[
          { id: 'dashboard', label: 'Dashboard', icon: BarChart2 },
          { id: 'users', label: 'Usuarios', icon: Users },
          { id: 'phrases', label: 'Frases', icon: FileText },
          { id: 'settings', label: 'Configuración', icon: Settings },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${
                  activeTab === tab.id
                    ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-200/50 dark:hover:bg-gray-700/50'
                }
              `}
            >
              <Icon className="h-4 w-4 mr-2" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'users' && renderUsers()}
        {activeTab === 'phrases' && (
          <Card className="p-6">
            <h2 className="text-xl font-bold mb-4">Gestión de Frases</h2>
            <p className="text-gray-500">Funcionalidad de gestión de frases en desarrollo...</p>
          </Card>
        )}
        {activeTab === 'settings' && (
          <Card className="p-6">
            <h2 className="text-xl font-bold mb-4">Configuración</h2>
            <p className="text-gray-500">
              Parámetros de verificación y reglas de negocio en desarrollo...
            </p>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export default AdminPage;
