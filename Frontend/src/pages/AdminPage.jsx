import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Users, BarChart3, Settings, Trash2, Edit } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const AdminPage = () => {
  const [activeTab, setActiveTab] = useState('users');

  // Datos de ejemplo
  const users = [
    { id: 1, name: 'Juan Pérez', email: 'juan@ejemplo.com', status: 'active', enrolled: true, lastLogin: '2024-11-14' },
    { id: 2, name: 'María García', email: 'maria@ejemplo.com', status: 'active', enrolled: false, lastLogin: '2024-11-13' },
    { id: 3, name: 'Carlos López', email: 'carlos@ejemplo.com', status: 'inactive', enrolled: true, lastLogin: '2024-11-10' },
  ];

  const stats = [
    { title: 'Total de Usuarios', value: '156', change: '+12%', trend: 'up' },
    { title: 'Usuarios Activos', value: '143', change: '+5%', trend: 'up' },
    { title: 'Verificaciones Hoy', value: '89', change: '+23%', trend: 'up' },
    { title: 'Tasa de Éxito', value: '94.2%', change: '+1.2%', trend: 'up' },
  ];

  const tabs = [
    { id: 'users', label: 'Usuarios', icon: Users },
    { id: 'stats', label: 'Estadísticas', icon: BarChart3 },
    { id: 'settings', label: 'Configuración', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Link 
              to="/dashboard" 
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mr-4"
            >
              <ArrowLeft className="h-5 w-5 mr-2" />
              Dashboard
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">
              Panel de Administración
            </h1>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    {stat.title}
                  </p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stat.value}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-sm font-medium text-green-600">
                    {stat.change}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => {
                const IconComponent = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <IconComponent className="h-5 w-5 mr-2" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'users' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">
                    Gestión de Usuarios
                  </h2>
                  <Button size="sm">
                    Agregar Usuario
                  </Button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Usuario
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Estado
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Perfil de Voz
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Último Acceso
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Acciones
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {users.map((user) => (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">
                                {user.name}
                              </div>
                              <div className="text-sm text-gray-500">
                                {user.email}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.status === 'active' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {user.status === 'active' ? 'Activo' : 'Inactivo'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                              user.enrolled 
                                ? 'bg-blue-100 text-blue-800' 
                                : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {user.enrolled ? 'Configurado' : 'Pendiente'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.lastLogin}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button className="text-blue-600 hover:text-blue-900">
                                <Edit className="h-4 w-4" />
                              </button>
                              <button className="text-red-600 hover:text-red-900">
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'stats' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">
                  Estadísticas del Sistema
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Verificaciones por Día
                    </h3>
                    <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                      <p className="text-gray-500">Gráfico de verificaciones</p>
                    </div>
                  </Card>
                  
                  <Card className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Tasa de Éxito
                    </h3>
                    <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
                      <p className="text-gray-500">Gráfico de tasa de éxito</p>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-6">
                  Configuración del Sistema
                </h2>
                <div className="space-y-6">
                  <Card className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Parámetros de Verificación
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Umbral de Confianza Mínimo
                        </label>
                        <input 
                          type="range" 
                          min="0" 
                          max="100" 
                          defaultValue="70"
                          className="w-full"
                        />
                        <span className="text-sm text-gray-500">70%</span>
                      </div>
                    </div>
                  </Card>
                  
                  <Card className="p-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">
                      Configuración de Grabación
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Calidad de Audio
                        </label>
                        <select className="block w-full px-3 py-2 border border-gray-300 rounded-md">
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