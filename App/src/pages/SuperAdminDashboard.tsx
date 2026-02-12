import { useState } from 'react';
import {
  LayoutDashboard,
  Building2,
  Users,
  Settings,
  Activity,
  Server,
  Shield,
  Search,
  Plus,
  MoreVertical,
  CheckCircle,
  XCircle,
  Database,
  Cpu,
} from 'lucide-react';
import MainLayout from '../components/ui/MainLayout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const SuperAdminDashboard = () => {
  const [activeSection, setActiveSection] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');

  // Mock Data
  const globalStats = [
    {
      title: 'Total Empresas',
      value: '12',
      change: '+2',
      trend: 'up',
      icon: Building2,
      color: 'blue',
    },
    {
      title: 'Usuarios Globales',
      value: '2,543',
      change: '+156',
      trend: 'up',
      icon: Users,
      color: 'purple',
    },
    {
      title: 'Verificaciones (Mes)',
      value: '15.2k',
      change: '+12.5%',
      trend: 'up',
      icon: Shield,
      color: 'emerald',
    },
    {
      title: 'Salud del Sistema',
      value: '99.9%',
      change: 'Stable',
      trend: 'neutral',
      icon: Activity,
      color: 'green',
    },
  ];

  const companies = [
    {
      id: 1,
      name: 'TechCorp Solutions',
      plan: 'Enterprise',
      users: 450,
      status: 'active',
      renewal: '2024-12-31',
    },
    {
      id: 2,
      name: 'Global Finance Inc',
      plan: 'Professional',
      users: 120,
      status: 'active',
      renewal: '2024-11-15',
    },
    {
      id: 3,
      name: 'StartUp Hub',
      plan: 'Starter',
      users: 15,
      status: 'inactive',
      renewal: '2024-10-01',
    },
  ];

  const renderSidebar = () => (
    <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 hidden lg:block">
      <div className="p-6">
        <h2 className="text-xl font-bold bg-linear-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          Super Admin
        </h2>
        <p className="text-xs text-gray-500 mt-1">Global Management</p>
      </div>
      <nav className="px-4 space-y-2">
        {[
          { id: 'overview', label: 'Vista General', icon: LayoutDashboard },
          { id: 'companies', label: 'Empresas', icon: Building2 },
          { id: 'users', label: 'Usuarios Globales', icon: Users },
          { id: 'system', label: 'Salud del Sistema', icon: Server },
          { id: 'settings', label: 'Configuración', icon: Settings },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              className={`w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                activeSection === item.id
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              <Icon className="h-5 w-5 mr-3" />
              {item.label}
            </button>
          );
        })}
      </nav>
    </div>
  );

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {globalStats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <Card key={index} className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className={`p-3 rounded-xl bg-${stat.color}-50 dark:bg-${stat.color}-900/20`}>
                  <Icon className={`h-6 w-6 text-${stat.color}-600 dark:text-${stat.color}-400`} />
                </div>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full ${
                    stat.trend === 'up'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {stat.change}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300">{stat.title}</p>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</h3>
            </Card>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
            Crecimiento de Empresas
          </h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-xl border border-dashed border-gray-200 dark:border-gray-700">
            <p className="text-gray-400">Gráfico de crecimiento aquí</p>
          </div>
        </Card>
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
            Distribución de Planes
          </h3>
          <div className="h-64 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-xl border border-dashed border-gray-200 dark:border-gray-700">
            <p className="text-gray-400">Gráfico circular aquí</p>
          </div>
        </Card>
      </div>
    </div>
  );

  const renderCompanies = () => (
    <Card className="p-6">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Gestión de Empresas</h2>
        <div className="flex gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:w-64">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar empresa..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Nueva Empresa
          </Button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Empresa
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Plan
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Usuarios
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Estado
              </th>
              <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Renovación
              </th>
              <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
            {companies.map((company) => (
              <tr key={company.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                  {company.name}
                </td>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                    {company.plan}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{company.users}</td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      company.status === 'active'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                    }`}
                  >
                    {company.status === 'active' ? (
                      <CheckCircle className="h-3 w-3 mr-1" />
                    ) : (
                      <XCircle className="h-3 w-3 mr-1" />
                    )}
                    {company.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{company.renewal}</td>
                <td className="py-3 px-4 text-right">
                  <Button variant="ghost" size="sm">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );

  const renderSystemHealth = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 border-t-4 border-green-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 dark:text-gray-100">API Server</h3>
            <Server className="h-5 w-5 text-green-500" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Uptime</span>
              <span className="font-medium text-green-600">99.99%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Latency</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">45ms</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Requests</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">1.2k/min</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-t-4 border-blue-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 dark:text-gray-100">Database</h3>
            <Database className="h-5 w-5 text-blue-500" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Status</span>
              <span className="font-medium text-green-600">Healthy</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Connections</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">85/100</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Size</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">1.4 GB</span>
            </div>
          </div>
        </Card>

        <Card className="p-6 border-t-4 border-purple-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 dark:text-gray-100">AI Engine</h3>
            <Cpu className="h-5 w-5 text-purple-500" />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Status</span>
              <span className="font-medium text-green-600">Operational</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Load</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">32%</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Queue</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">0 jobs</span>
            </div>
          </div>
        </Card>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">System Logs</h3>
        <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs h-64 overflow-y-auto">
          <p>[2024-11-30 14:45:22] INFO: API Gateway started on port 3000</p>
          <p>[2024-11-30 14:45:23] INFO: Database connection established</p>
          <p>[2024-11-30 14:45:25] INFO: AI Model loaded successfully (250ms)</p>
          <p>[2024-11-30 14:46:01] INFO: Incoming request GET /api/verify</p>
          <p>[2024-11-30 14:46:02] SUCCESS: Verification completed for user_123</p>
          <p>[2024-11-30 14:48:15] WARN: High latency detected on node-3</p>
          <p>[2024-11-30 14:50:00] INFO: Scheduled backup completed</p>
        </div>
      </Card>
    </div>
  );

  return (
    <MainLayout>
      <div className="flex flex-col lg:flex-row gap-6">
        {renderSidebar()}
        <div className="flex-1">
          <div className="mb-8 lg:hidden">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Super Admin</h1>
          </div>

          <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
            {activeSection === 'overview' && renderOverview()}
            {activeSection === 'companies' && renderCompanies()}
            {activeSection === 'system' && renderSystemHealth()}
            {activeSection === 'users' && (
              <Card className="p-6">
                <h2 className="text-xl font-bold mb-4">Usuarios Globales</h2>
                <p className="text-gray-500">Gestión de usuarios a nivel global en desarrollo...</p>
              </Card>
            )}
            {activeSection === 'settings' && (
              <Card className="p-6">
                <h2 className="text-xl font-bold mb-4">Configuración Global</h2>
                <p className="text-gray-500">Configuración del sistema SaaS en desarrollo...</p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default SuperAdminDashboard;
