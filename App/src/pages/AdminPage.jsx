import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Users, BarChart3, Settings, Trash2, Edit } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { adminService } from '../services/apiServices';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const AdminPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        const [usersData, statsData] = await Promise.all([
          adminService.getUsers(1, 50), // página 1, 50 usuarios por página
          adminService.getSystemStats()
        ]);

        // Filtrar usuarios según el rol del usuario actual
        let filteredUsers = usersData.users;
        if (user?.role === 'admin' && user?.company) {
          // Los administradores solo ven usuarios de su empresa
          filteredUsers = usersData.users.filter(u => u.company === user.company);
        }
        // Los superadmin ven todos los usuarios

        setUsers(filteredUsers);
        setStats([
          { title: 'Total de Usuarios', value: filteredUsers.length.toString(), change: '+12%', trend: 'up' },
          { title: 'Usuarios Activos', value: statsData.active_users.toString(), change: '+5%', trend: 'up' },
          { title: 'Verificaciones Hoy', value: statsData.verifications_today.toString(), change: '+23%', trend: 'up' },
          { title: 'Tasa de Éxito', value: `${statsData.success_rate}%`, change: '+1.2%', trend: 'up' },
        ]);
      } catch (error) {
        console.error('Error loading admin data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [user?.role, user?.company]);

  const tabs = [
    { id: 'users', label: 'Usuarios', icon: Users },
    { id: 'stats', label: 'Estadísticas', icon: BarChart3 },
    { id: 'settings', label: 'Configuración', icon: Settings },
  ];

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/20 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Link 
              to="/dashboard" 
              className="flex items-center px-4 py-2 text-blue-600 hover:text-blue-700 transition-all duration-300 bg-white/70 backdrop-blur-xl border border-blue-200/40 rounded-xl hover:bg-white/80 hover:shadow-md mr-4"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Dashboard
            </Link>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-purple-800 bg-clip-text text-transparent">
              Panel de Administración
            </h1>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} variant="glass" className="p-6 shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-[1.02]">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600/70 mb-2">
                    {stat.title}
                  </p>
                  <p className="text-3xl font-bold text-gray-800">
                    {stat.value}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-semibold text-emerald-600 bg-emerald-50/80 px-2 py-1 rounded-lg">
                    {stat.change}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Tabs */}
        <div className="backdrop-blur-xl bg-white/70 border border-blue-200/40 rounded-2xl shadow-xl">
          <div className="border-b border-blue-200/40">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-4 border-b-2 font-semibold text-sm flex items-center transition-all duration-300 ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600 bg-blue-50/60'
                        : 'border-transparent text-gray-600 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50/30'
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
            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent">
                    Gestión de Usuarios
                    {user?.role === 'admin' && user?.company && (
                      <span className="text-base font-normal text-blue-600/70 ml-2">
                        - {user.company}
                      </span>
                    )}
                  </h2>
                  <Button size="sm" className="shadow-lg">
                    Agregar Usuario
                  </Button>
                </div>
                
                {isLoading ? (
                  <div className="backdrop-blur-sm bg-white/80 border border-blue-200/40 rounded-xl shadow-lg p-8 text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Cargando usuarios...</p>
                  </div>
                ) : (
                  <div className="backdrop-blur-sm bg-white/80 border border-blue-200/40 rounded-xl shadow-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-blue-200/30">
                      <thead className="bg-gradient-to-r from-blue-50/80 to-indigo-50/80">
                        <tr>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                            Usuario
                          </th>
                          {user?.role === 'superadmin' && (
                            <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                              Empresa
                            </th>
                          )}
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                            Rol
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                            Estado
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                            Perfil de Voz
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                            Último Acceso
                          </th>
                          <th className="px-6 py-4 text-left text-xs font-bold text-blue-800 uppercase tracking-wider">
                            Acciones
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-blue-200/20">
                      {users.map((userItem) => (
                        <tr key={userItem.id} className="hover:bg-blue-50/40 transition-colors duration-200">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-semibold text-gray-800">
                                {userItem.name}
                              </div>
                              <div className="text-sm text-blue-600/70">
                                {userItem.email}
                              </div>
                            </div>
                          </td>
                          {user?.role === 'superadmin' && (
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-800">
                                {userItem.company || 'N/A'}
                              </div>
                            </td>
                          )}
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full backdrop-blur-sm ${
                              userItem.role === 'superadmin' 
                                ? 'bg-red-100/80 text-red-700 border border-red-200/40' 
                                : userItem.role === 'admin'
                                ? 'bg-orange-100/80 text-orange-700 border border-orange-200/40'
                                : 'bg-green-100/80 text-green-700 border border-green-200/40'
                            }`}>
                              {userItem.role === 'superadmin' ? 'Super Admin' : 
                               userItem.role === 'admin' ? 'Admin' : 'Usuario'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full backdrop-blur-sm ${
                              userItem.status === 'active' 
                                ? 'bg-emerald-100/80 text-emerald-700 border border-emerald-200/40' 
                                : 'bg-red-100/80 text-red-700 border border-red-200/40'
                            }`}>
                              {userItem.status === 'active' ? 'Activo' : 'Inactivo'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full backdrop-blur-sm ${
                              (userItem.voice_template || userItem.enrolled)
                                ? 'bg-blue-100/80 text-blue-700 border border-blue-200/40' 
                                : 'bg-amber-100/80 text-amber-700 border border-amber-200/40'
                            }`}>
                              {(userItem.voice_template || userItem.enrolled) ? 'Configurado' : 'Pendiente'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-medium">
                            {userItem.created_at ? new Date(userItem.created_at).toLocaleDateString() : (userItem.lastLogin || 'N/A')}
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
                    <h3 className="text-lg font-bold text-gray-800 mb-4">
                      Verificaciones por Día
                    </h3>
                    <div className="h-64 bg-gradient-to-br from-blue-50/60 to-indigo-50/60 border border-blue-200/40 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <p className="text-blue-600 font-medium">📊 Gráfico de verificaciones</p>
                    </div>
                  </Card>
                  
                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">
                      Tasa de Éxito
                    </h3>
                    <div className="h-64 bg-gradient-to-br from-green-50/60 to-emerald-50/60 border border-green-200/40 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <p className="text-green-600 font-medium">📈 Gráfico de tasa de éxito</p>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-6">
                  Configuración del Sistema
                </h2>
                <div className="space-y-6">
                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">
                      Parámetros de Verificación
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-3">
                          Umbral de Confianza Mínimo
                        </label>
                        <input 
                          type="range" 
                          min="0" 
                          max="100" 
                          defaultValue="70"
                          className="w-full h-2 bg-blue-100/60 rounded-lg appearance-none cursor-pointer slider"
                        />
                        <span className="text-sm font-medium text-blue-600 bg-blue-50/80 px-2 py-1 rounded-lg">70%</span>
                      </div>
                    </div>
                  </Card>
                  
                  <Card variant="glass" className="p-6 shadow-xl">
                    <h3 className="text-lg font-bold text-gray-800 mb-4">
                      Configuración de Grabación
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-3">
                          Calidad de Audio
                        </label>
                        <select className="block w-full px-4 py-3 border border-blue-200/50 bg-white/80 backdrop-blur-sm rounded-xl text-gray-800 font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/60 transition-all duration-300">
                          <option>Alta (48kHz)</option>
                          <option>Media (24kHz)</option>
                          <option>Básica (16kHz)</option>
                        </select>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;