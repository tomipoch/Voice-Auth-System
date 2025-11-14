import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Mic, 
  Shield, 
  Users, 
  LogOut, 
  Settings,
  Home,
  UserCheck,
  UserPlus as UserPlusIcon
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('home');

  const handleLogout = async () => {
    await logout();
  };

  const navigation = [
    { id: 'home', label: 'Inicio', icon: Home },
    { id: 'enrollment', label: 'Registro de Voz', icon: UserPlusIcon, href: '/enrollment' },
    { id: 'verification', label: 'Verificación', icon: UserCheck, href: '/verification' },
  ];

  // Agregar navegación de admin si el usuario es administrador
  if (user?.role === 'admin') {
    navigation.push(
      { id: 'admin', label: 'Administración', icon: Users, href: '/admin' }
    );
  }

  const stats = [
    {
      title: 'Verificaciones Hoy',
      value: '24',
      icon: Shield,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Registro de Voz',
      value: user?.voice_template ? 'Configurado' : 'Pendiente',
      icon: Mic,
      color: user?.voice_template ? 'text-green-600' : 'text-orange-600',
      bgColor: user?.voice_template ? 'bg-green-50' : 'bg-orange-50',
    },
    {
      title: 'Estado de Seguridad',
      value: 'Activo',
      icon: Shield,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center px-6 py-4 border-b border-gray-200">
            <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Mic className="h-6 w-6 text-white" />
            </div>
            <h1 className="ml-3 text-xl font-bold text-gray-900">VoiceAuth</h1>
          </div>

          {/* User Info */}
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                <span className="text-sm font-medium text-gray-700">
                  {user?.name?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                <p className="text-xs text-gray-500">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-2">
            {navigation.map((item) => {
              const IconComponent = item.icon;
              const isActive = item.id === activeTab;
              
              if (item.href) {
                return (
                  <Link
                    key={item.id}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    <IconComponent className="h-5 w-5 mr-3" />
                    {item.label}
                  </Link>
                );
              }

              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <IconComponent className="h-5 w-5 mr-3" />
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-4 py-4 border-t border-gray-200 space-y-2">
            <button className="w-full flex items-center px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors">
              <Settings className="h-5 w-5 mr-3" />
              Configuración
            </button>
            <Button
              variant="secondary"
              size="sm"
              className="w-full"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Cerrar Sesión
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">
              Bienvenido, {user?.name}
            </h1>
            <p className="text-gray-600 mt-2">
              Panel de control de autenticación biométrica por voz
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {stats.map((stat, index) => {
              const IconComponent = stat.icon;
              return (
                <Card key={index} className="p-6">
                  <div className="flex items-center">
                    <div className={`p-3 rounded-lg ${stat.bgColor}`}>
                      <IconComponent className={`h-6 w-6 ${stat.color}`} />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-500">
                        {stat.title}
                      </p>
                      <p className="text-lg font-semibold text-gray-900">
                        {stat.value}
                      </p>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>

          {/* Quick Actions */}
          <Card className="p-6">
            <Card.Header>
              <Card.Title>Acciones Rápidas</Card.Title>
            </Card.Header>
            <Card.Content>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {!user?.voice_template && (
                  <Link to="/enrollment">
                    <div className="p-4 border-2 border-dashed border-orange-300 rounded-lg hover:border-orange-400 transition-colors">
                      <div className="flex items-center">
                        <UserPlusIcon className="h-8 w-8 text-orange-600 mr-4" />
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            Configurar Voz
                          </h3>
                          <p className="text-sm text-gray-500">
                            Registra tu perfil de voz para usar el sistema
                          </p>
                        </div>
                      </div>
                    </div>
                  </Link>
                )}
                
                <Link to="/verification">
                  <div className="p-4 border-2 border-dashed border-blue-300 rounded-lg hover:border-blue-400 transition-colors">
                    <div className="flex items-center">
                      <UserCheck className="h-8 w-8 text-blue-600 mr-4" />
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">
                          Verificar Identidad
                        </h3>
                        <p className="text-sm text-gray-500">
                          Autentícate usando tu voz
                        </p>
                      </div>
                    </div>
                  </div>
                </Link>
              </div>
            </Card.Content>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;