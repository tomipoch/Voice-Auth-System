import { useState, useEffect } from 'react';
import {
  Users,
  BarChart3,
  Settings,
  Shield,
  CheckCircle,
  XCircle,
  TrendingUp,
  Activity,
  Mic,
  Edit,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { adminService } from '../services/apiServices';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import MainLayout from '../components/ui/MainLayout';

interface UserItem {
  id: string;
  email: string;
  username: string;
  fullName: string;
  role: 'user' | 'admin' | 'super_admin';
  isVerified: boolean;
  voiceProfile?: any;
  createdAt: string;
  updatedAt: string;
}

interface StatCard {
  title: string;
  value: string;
  change: string;
  trend: string;
  icon: any;
  color: string;
}

const AdminPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [users, setUsers] = useState<UserItem[]>([]);
  const [stats, setStats] = useState<StatCard[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        const [usersData, statsData] = await Promise.all([
          adminService.getUsers(1, 50),
          adminService.getStats(),
        ]);

        // Filtrar solo usuarios de la empresa del admin
        let filteredUsers = usersData.data;

        setUsers(filteredUsers);
        setStats([
          {
            title: 'Total de Usuarios',
            value: filteredUsers.length.toString(),
            change: '+12%',
            trend: 'up',
            icon: Users,
            color: 'blue',
          },
          {
            title: 'Con Perfil de Voz',
            value: filteredUsers.filter((u) => u.voiceProfile).length.toString(),
            change: '+8%',
            trend: 'up',
            icon: Mic,
            color: 'purple',
          },
          {
            title: 'Verificaciones Hoy',
            value: statsData.totalVerifications.toString(),
            change: '+23%',
            trend: 'up',
            icon: Activity,
            color: 'green',
          },
          {
            title: 'Tasa de Éxito',
            value: `${statsData.successRate.toFixed(1)}%`,
            change: '+2%',
            trend: 'up',
            icon: TrendingUp,
            color: 'emerald',
          },
        ]);
      } catch (error) {
        console.error('Error loading admin data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [user?.role]);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'users', label: 'Usuarios', icon: Users },
    { id: 'settings', label: 'Configuración', icon: Settings },
  ];

  const getColorClasses = (color: string) => {
    const colors: any = {
      blue: 'from-blue-500 to-blue-600 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
      purple:
        'from-purple-500 to-purple-600 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400',
      green:
        'from-green-500 to-green-600 bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400',
      emerald:
        'from-emerald-500 to-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    };
    return colors[color] || colors.blue;
  };

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-purple-800 dark:from-gray-200 dark:via-blue-400/70 dark:to-purple-400/70 bg-clip-text text-transparent">
              Panel de Administración
            </h1>
            <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium mt-2">
              Gestión de usuarios y configuración de empresa
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {user?.fullName || user?.username}
            </p>
            <p className="text-xs text-blue-600/70 dark:text-blue-400/70">Administrador</p>
          </div>
        </div>
      </div>

        {/* Stats Dashboard - Solo visible en tab dashboard */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => {
              const IconComponent = stat.icon;
              const colorClasses = getColorClasses(stat.color);
              return (
                <Card
                  key={index}
                  variant="glass"
                  className="p-6 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClasses.split(' ')[0]} ${colorClasses.split(' ')[1]} flex items-center justify-center shadow-lg`}
                    >
                      <IconComponent className="h-6 w-6 text-white" />
                    </div>
                  </div>
                  <p className="text-sm font-medium text-gray-600 dark:text-blue-400/70 mb-1">
                    {stat.title}
                  </p>
                  <p className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-2">
                    {stat.value}
                  </p>
                  <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50/80 dark:bg-emerald-900/30 px-2 py-1 rounded-lg">
                    {stat.change} vs mes anterior
                  </span>
                </Card>
              );
            })}
          </div>
        )}

        {/* Tabs */}
        <div className="backdrop-blur-xl bg-white dark:bg-gray-800/70 border border-blue-200/40 dark:border-gray-600/40 rounded-2xl shadow-xl">
          <div className="border-b border-blue-200/40 dark:border-gray-600/40">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-4 border-b-2 font-semibold text-sm flex items-center transition-all duration-300 ${
                      activeTab === tab.id
                        ? 'border-blue-500 dark:border-blue-400 text-blue-600 dark:text-blue-400/70 bg-blue-50/60 dark:bg-gray-700/50'
                        : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400/70 hover:border-blue-300 dark:hover:border-gray-600 hover:bg-blue-50/30 dark:hover:bg-gray-700/30'
                    }`}
                  >
                    <IconComponent className="h-5 w-5 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-8">
            {activeTab === 'dashboard' && (
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400/70 bg-clip-text text-transparent mb-6">
                  Resumen de la Empresa
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                      <Activity className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
                      Actividad Reciente
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-blue-50/60 dark:bg-gray-700/50 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                            Verificaciones hoy
                          </p>
                          <p className="text-xs text-blue-600/70 dark:text-blue-400/70">
                            Último acceso hace 5 min
                          </p>
                        </div>
                        <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                          {stats[2]?.value || '0'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-purple-50/60 dark:bg-gray-700/50 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                            Usuarios con voz
                          </p>
                          <p className="text-xs text-purple-600/70 dark:text-purple-400/70">
                            Registros completos
                          </p>
                        </div>
                        <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                          {stats[1]?.value || '0'}
                        </span>
                      </div>
                    </div>
                  </Card>

                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                      <Shield className="h-5 w-5 mr-2 text-emerald-600 dark:text-emerald-400" />
                      Estado del Sistema
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-emerald-50/60 dark:bg-gray-700/50 rounded-lg">
                        <div className="flex items-center">
                          <CheckCircle className="h-5 w-5 text-emerald-600 dark:text-emerald-400 mr-2" />
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                            Sistema operativo
                          </p>
                        </div>
                        <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-100/80 dark:bg-emerald-900/30 px-2 py-1 rounded">
                          100% Uptime
                        </span>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-blue-50/60 dark:bg-gray-700/50 rounded-lg">
                        <div className="flex items-center">
                          <Mic className="h-5 w-5 text-blue-600 dark:text-blue-400 mr-2" />
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                            Servicio de voz
                          </p>
                        </div>
                        <span className="text-xs font-semibold text-blue-600 dark:text-blue-400 bg-blue-100/80 dark:bg-blue-900/30 px-2 py-1 rounded">
                          Activo
                        </span>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400/70 bg-clip-text text-transparent">
                    Gestión de Usuarios
                  </h2>
                  <Button size="sm" className="shadow-lg">
                    Agregar Usuario
                  </Button>
                </div>

                {isLoading ? (
                  <div className="backdrop-blur-sm bg-white dark:bg-gray-800/70 border border-blue-200/40 dark:border-gray-600/40 rounded-xl shadow-lg p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400 mx-auto mb-4"></div>
                    <p className="text-gray-600 dark:text-blue-400/70">Cargando usuarios...</p>
                  </div>
                ) : (
                  <div className="backdrop-blur-sm bg-white dark:bg-gray-800/70 border border-blue-200/40 dark:border-gray-600/40 rounded-xl shadow-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-blue-200/30 dark:divide-gray-600/30">
                      <thead className="bg-gradient-to-r from-blue-50/80 to-indigo-50/80 dark:from-gray-700/50 dark:to-gray-700/50">
                        <tr>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 dark:text-blue-400/70 uppercase tracking-wider">
                            Usuario
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 dark:text-blue-400/70 uppercase tracking-wider">
                            Rol
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 dark:text-blue-400/70 uppercase tracking-wider">
                            Estado
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 dark:text-blue-400/70 uppercase tracking-wider">
                            Perfil de Voz
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 dark:text-blue-400/70 uppercase tracking-wider">
                            Acciones
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-blue-200/20">
                        {users.map((userItem) => (
                          <tr
                            key={userItem.id}
                            className="hover:bg-blue-50/40 transition-colors duration-200"
                          >
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div>
                                <div className="text-sm font-semibold text-gray-800">
                                  {userItem.fullName}
                                </div>
                                <div className="text-sm text-blue-600/70">{userItem.email}</div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span
                                className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full backdrop-blur-sm ${
                                  userItem.role === 'super_admin'
                                    ? 'bg-red-100/80 text-red-700 border border-red-200/40'
                                    : userItem.role === 'admin'
                                      ? 'bg-orange-100/80 text-orange-700 border border-orange-200/40'
                                      : 'bg-green-100/80 text-green-700 border border-green-200/40'
                                }`}
                              >
                                {userItem.role === 'super_admin'
                                  ? 'Super Admin'
                                  : userItem.role === 'admin'
                                    ? 'Admin'
                                    : 'Usuario'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span
                                className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full backdrop-blur-sm ${
                                  userItem.isVerified
                                    ? 'bg-emerald-100/80 text-emerald-700 border border-emerald-200/40'
                                    : 'bg-red-100/80 text-red-700 border border-red-200/40'
                                }`}
                              >
                                {userItem.isVerified ? 'Activo' : 'Inactivo'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span
                                className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full backdrop-blur-sm ${
                                  userItem.voiceProfile
                                    ? 'bg-blue-100/80 text-blue-700 border border-blue-200/40'
                                    : 'bg-amber-100/80 text-amber-700 border border-amber-200/40'
                                }`}
                              >
                                {userItem.voiceProfile ? 'Configurado' : 'Pendiente'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 font-medium">
                              {userItem.createdAt
                                ? new Date(userItem.createdAt).toLocaleDateString()
                                : 'N/A'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              <div className="flex space-x-2">
                                <button className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50/60 rounded-lg transition-all duration-200">
                                  <Edit className="h-4 w-4" />
                                </button>
                                <button className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50/60 rounded-lg transition-all duration-200">
                                  <Trash2 className="h-4 w-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'stats' && (
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-6">
                  Estadísticas del Sistema
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">Verificaciones por Día</h3>
                    <div className="h-64 bg-gradient-to-br from-blue-50/60 to-indigo-50/60 border border-blue-200/40 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <p className="text-blue-600 font-medium">📊 Gráfico de verificaciones</p>
                    </div>
                  </Card>

                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">Tasa de Éxito</h3>
                    <div className="h-64 bg-gradient-to-br from-green-50/60 to-emerald-50/60 border border-green-200/40 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <p className="text-green-600 font-medium">📈 Gráfico de tasa de éxito</p>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400/70 bg-clip-text text-transparent mb-6">
                  Configuración de la Empresa
                </h2>
                <div className="space-y-6">
                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                      <Shield className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
                      Parámetros de Verificación
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                          Umbral de Confianza Mínimo
                        </label>
                        <div className="flex items-center gap-4">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            defaultValue="70"
                            className="flex-1 h-2 bg-blue-100/60 dark:bg-gray-700/50 rounded-lg appearance-none cursor-pointer"
                          />
                          <span className="text-sm font-medium text-blue-600 dark:text-blue-400 bg-blue-50/80 dark:bg-blue-900/30 px-3 py-1 rounded-lg min-w-[60px] text-center">
                            70%
                          </span>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-blue-400/70 mt-2">
                          Porcentaje mínimo de similitud requerido para aceptar una verificación
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                          Intentos Máximos de Verificación
                        </label>
                        <select className="block w-full px-4 py-3 border border-blue-200/50 dark:border-gray-600/40 bg-white/80 dark:bg-gray-800/70 backdrop-blur-sm rounded-xl text-gray-800 dark:text-gray-200 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60 transition-all duration-300">
                          <option>3 intentos</option>
                          <option>5 intentos</option>
                          <option>10 intentos</option>
                        </select>
                      </div>
                    </div>
                  </Card>

                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                      <Mic className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" />
                      Configuración de Audio
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                          Calidad de Grabación
                        </label>
                        <select className="block w-full px-4 py-3 border border-blue-200/50 dark:border-gray-600/40 bg-white/80 dark:bg-gray-800/70 backdrop-blur-sm rounded-xl text-gray-800 dark:text-gray-200 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60 transition-all duration-300">
                          <option>Alta (48kHz)</option>
                          <option>Media (24kHz)</option>
                          <option>Básica (16kHz)</option>
                        </select>
                        <p className="text-xs text-gray-600 dark:text-blue-400/70 mt-2">
                          Mayor calidad requiere más ancho de banda
                        </p>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                          Duración Mínima de Grabación
                        </label>
                        <select className="block w-full px-4 py-3 border border-blue-200/50 dark:border-gray-600/40 bg-white/80 dark:bg-gray-800/70 backdrop-blur-sm rounded-xl text-gray-800 dark:text-gray-200 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60 transition-all duration-300">
                          <option>3 segundos</option>
                          <option>5 segundos</option>
                          <option>10 segundos</option>
                        </select>
                      </div>
                    </div>
                  </Card>

                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                      <Settings className="h-5 w-5 mr-2 text-emerald-600 dark:text-emerald-400" />
                      Configuración General
                    </h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between p-4 bg-blue-50/60 dark:bg-gray-700/50 rounded-lg">
                        <div>
                          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                            Notificaciones por Email
                          </p>
                          <p className="text-xs text-gray-600 dark:text-blue-400/70">
                            Recibir alertas sobre verificaciones fallidas
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input type="checkbox" className="sr-only peer" defaultChecked />
                          <div className="w-11 h-6 bg-gray-300 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                      <div className="flex items-center justify-between p-4 bg-blue-50/60 dark:bg-gray-700/50 rounded-lg">
                        <div>
                          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200">
                            Modo Estricto
                          </p>
                          <p className="text-xs text-gray-600 dark:text-blue-400/70">
                            Requerir re-verificación después de período de inactividad
                          </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input type="checkbox" className="sr-only peer" />
                          <div className="w-11 h-6 bg-gray-300 dark:bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                        </label>
                      </div>
                    </div>
                  </Card>

                  <div className="flex justify-end gap-3">
                    <Button
                      variant="secondary"
                      className="px-6 py-2"
                    >
                      Cancelar
                    </Button>
                    <Button
                      variant="primary"
                      className="px-6 py-2"
                    >
                      Guardar Cambios
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </MainLayout>
  );
};

export default AdminPage;
