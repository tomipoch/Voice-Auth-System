import { useState } from 'react';
import {
  Shield,
  Users,
  Building2,
  LogOut,
  Settings,
  Home,
  TrendingUp,
  AlertTriangle,
  Server,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { useDashboardStats } from '../hooks/useDashboardStats';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const SuperAdminDashboard = () => {
  const { user, logout } = useAuth();
  const { systemStats, isLoading } = useDashboardStats();
  const [activeTab, setActiveTab] = useState('overview');

  const handleLogout = async () => {
    await logout();
  };

  const navigation = [
    { id: 'overview', label: 'Vista General', icon: Home },
    { id: 'companies', label: 'Empresas', icon: Building2 },
    { id: 'users', label: 'Usuarios Globales', icon: Users },
    { id: 'system', label: 'Sistema', icon: Server },
    { id: 'settings', label: 'Configuración', icon: Settings },
  ];

  // Estadísticas específicas del super admin
  const superAdminStats = [
    {
      title: 'Total Empresas',
      value: '3',
      icon: Building2,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      change: '+1',
    },
    {
      title: 'Usuarios Globales',
      value: isLoading ? '...' : '12',
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      change: '+4',
    },
    {
      title: 'Verificaciones Hoy',
      value: isLoading ? '...' : systemStats?.totalVerifications?.toString() || '0',
      icon: Shield,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      change: '+23%',
    },
    {
      title: 'Uptime del Sistema',
      value: '99.9%',
      icon: TrendingUp,
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
      change: '+0.1%',
    },
  ];

  // Datos de empresas
  const companiesData = [
    {
      id: 1,
      name: 'Empresa A',
      users: 5,
      status: 'active',
      lastActivity: '2024-11-15',
      plan: 'Enterprise',
      verifications: 156,
    },
    {
      id: 2,
      name: 'Empresa B',
      users: 4,
      status: 'active',
      lastActivity: '2024-11-14',
      plan: 'Professional',
      verifications: 98,
    },
    {
      id: 3,
      name: 'Test Company',
      users: 3,
      status: 'trial',
      lastActivity: '2024-11-13',
      plan: 'Trial',
      verifications: 23,
    },
  ];

  // Alertas del sistema
  const systemAlerts = [
    {
      id: 1,
      type: 'warning',
      title: 'Alta carga en servidor',
      message: 'El servidor está experimentando un 85% de uso de CPU',
      timestamp: '2024-11-15 10:30',
    },
    {
      id: 2,
      type: 'info',
      title: 'Actualización programada',
      message: 'Mantenimiento programado para el 16/11 a las 2:00 AM',
      timestamp: '2024-11-14 14:20',
    },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden bg-linear-to-br from-purple-50 via-indigo-50 to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-400/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-600/20 dark:bg-indigo-600/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-400/20 dark:bg-blue-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Sidebar with Liquid Glass Effect */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 backdrop-blur-xl bg-white dark:bg-gray-800/70 border-r border-purple-200/40 dark:border-gray-600/40 shadow-xl">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-4 border-b border-purple-200/30 dark:border-gray-600/30">
            <div className="h-12 w-12 bg-linear-to-br from-purple-500 to-indigo-600 dark:from-purple-600 dark:to-indigo-700 rounded-2xl flex items-center justify-center shadow-lg">
              <Shield className="h-7 w-7 text-white" />
            </div>
            <h1 className="ml-3 text-xl font-bold bg-linear-to-r from-gray-800 to-purple-700 dark:from-gray-200 dark:to-purple-400/70 bg-clip-text text-transparent">
              Super Admin
            </h1>
          </div>

          {/* User Info */}
          <div className="px-6 py-4 border-b border-purple-200/30 dark:border-gray-600/30">
            <div className="flex items-center">
              <div className="h-12 w-12 bg-linear-to-br from-purple-100 to-indigo-100 dark:from-purple-900/50 dark:to-indigo-900/50 rounded-xl flex items-center justify-center shadow-sm border border-purple-200/40 dark:border-purple-600/40">
                <span className="text-lg font-bold bg-linear-to-r from-purple-600 to-indigo-600 dark:from-purple-400 dark:to-indigo-400 bg-clip-text text-transparent">
                  {(user?.fullName || user?.username || 'S').charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                  {user?.fullName || user?.username}
                </p>
                <p className="text-xs text-purple-600/70 dark:text-purple-400/70">{user?.email}</p>
                <span className="inline-block text-xs px-2 py-1 rounded-md mt-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-700/60">
                  Super Administrador
                </span>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {navigation.map((item) => {
              const IconComponent = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-300 ${
                    activeTab === item.id
                      ? 'bg-linear-to-r from-purple-500 to-indigo-600 dark:from-purple-600 dark:to-indigo-700 text-white shadow-lg'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-purple-50/60 dark:hover:bg-gray-700/50 hover:text-purple-700 dark:hover:text-purple-400'
                  }`}
                >
                  <IconComponent className="h-5 w-5 mr-3" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="px-4 py-4 border-t border-purple-200/30 dark:border-gray-600/30">
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full flex items-center justify-center border-purple-200/40 dark:border-gray-600/40 text-purple-700 dark:text-purple-400 hover:bg-purple-50/60 dark:hover:bg-gray-700/50"
            >
              <LogOut className="h-5 w-5 mr-2" />
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 relative z-10">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 to-purple-700 dark:from-gray-200 dark:to-purple-400/70 bg-clip-text text-transparent">
                Panel de Super Administrador
              </h1>
              <p className="text-purple-600/70 dark:text-purple-400/70 mt-2">
                Gestión global del sistema VoiceAuth
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                  Sistema Global
                </p>
                <p className="text-xs text-purple-600 dark:text-purple-400/70">Acceso Completo</p>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {superAdminStats.map((stat, index) => {
              const IconComponent = stat.icon;
              return (
                <Card
                  key={index}
                  variant="glass"
                  className="p-6 shadow-xl backdrop-blur-xl border border-purple-200/40 dark:border-gray-600/40"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-gray-600 dark:text-blue-400/70 mb-2">
                        {stat.title}
                      </p>
                      <p className="text-2xl font-bold text-gray-800 dark:text-gray-200">
                        {stat.value}
                      </p>
                    </div>
                    <div
                      className={`h-12 w-12 ${stat.bgColor} dark:bg-gray-700/50 rounded-xl flex items-center justify-center shadow-sm`}
                    >
                      <IconComponent className={`h-6 w-6 ${stat.color} dark:text-blue-400/70`} />
                    </div>
                  </div>
                  <div className="mt-4 flex items-center">
                    <span className="text-sm font-semibold text-green-600 dark:text-green-400 bg-green-50/80 dark:bg-green-900/30 px-2 py-1 rounded-lg">
                      {stat.change}
                    </span>
                    <span className="text-sm text-gray-500 dark:text-blue-400/70 ml-2">
                      vs mes anterior
                    </span>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Main Content Area */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Companies Overview */}
            {activeTab === 'overview' && (
              <>
                <div className="lg:col-span-2">
                  <Card
                    variant="glass"
                    className="p-6 shadow-xl backdrop-blur-xl border border-purple-200/40"
                  >
                    <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
                      <Building2 className="h-5 w-5 mr-2 text-purple-600" />
                      Empresas Registradas
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="min-w-full">
                        <thead>
                          <tr className="border-b border-purple-200/30">
                            <th className="text-left text-xs font-bold text-purple-800 uppercase tracking-wider pb-3">
                              Empresa
                            </th>
                            <th className="text-left text-xs font-bold text-purple-800 uppercase tracking-wider pb-3">
                              Usuarios
                            </th>
                            <th className="text-left text-xs font-bold text-purple-800 uppercase tracking-wider pb-3">
                              Estado
                            </th>
                            <th className="text-left text-xs font-bold text-purple-800 uppercase tracking-wider pb-3">
                              Plan
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-purple-200/20">
                          {companiesData.map((company) => (
                            <tr key={company.id} className="hover:bg-purple-50/40">
                              <td className="py-4">
                                <div className="font-medium text-gray-800">{company.name}</div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  {company.lastActivity}
                                </div>
                              </td>
                              <td className="py-4 text-sm text-gray-800">{company.users}</td>
                              <td className="py-4">
                                <span
                                  className={`px-3 py-1 text-xs font-semibold rounded-full ${
                                    company.status === 'active'
                                      ? 'bg-green-100 text-green-800'
                                      : 'bg-yellow-100 text-yellow-800'
                                  }`}
                                >
                                  {company.status === 'active' ? 'Activo' : 'Prueba'}
                                </span>
                              </td>
                              <td className="py-4 text-sm text-gray-800">{company.plan}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </div>

                {/* System Alerts */}
                <div>
                  <Card
                    variant="glass"
                    className="p-6 shadow-xl backdrop-blur-xl border border-purple-200/40"
                  >
                    <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
                      <AlertTriangle className="h-5 w-5 mr-2 text-yellow-600" />
                      Alertas del Sistema
                    </h3>
                    <div className="space-y-4">
                      {systemAlerts.map((alert) => (
                        <div
                          key={alert.id}
                          className={`p-4 rounded-lg border ${
                            alert.type === 'warning'
                              ? 'bg-yellow-50/80 border-yellow-200'
                              : 'bg-blue-50/80 border-blue-200'
                          }`}
                        >
                          <h4 className="font-medium text-gray-800 text-sm">{alert.title}</h4>
                          <p className="text-xs text-gray-600 mt-1">{alert.message}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            {alert.timestamp}
                          </p>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SuperAdminDashboard;
