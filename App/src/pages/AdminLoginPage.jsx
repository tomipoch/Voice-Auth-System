import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Lock, User, Eye, EyeOff, AlertCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';
import { logger } from '../config/environment.js';

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const { login, logout } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Credenciales de ejemplo para administradores
  const adminCredentials = [
    { email: 'superadmin@voicebio.com', role: 'Super Administrador' },
    { email: 'admin@empresaa.com', role: 'Administrador - Empresa A' },
    { email: 'admin@empresab.com', role: 'Administrador - Empresa B' },
    { email: 'admin@test.com', role: 'Admin Desarrollo' },
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    if (error) setError('');
  };

  const validateAdminEmail = (email) => {
    const adminEmails = [
      'superadmin@voicebio.com',
      'admin@empresaa.com', 
      'admin@empresab.com',
      'admin@test.com'
    ];
    return adminEmails.includes(email.toLowerCase());
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Validar que sea un email de administrador
      if (!validateAdminEmail(formData.email)) {
        throw new Error('Este email no tiene permisos administrativos. Use el login regular para usuarios normales.');
      }

      logger.info('Admin login attempt:', { email: formData.email });
      
      const response = await login(formData.email, formData.password);
      
      // Redirigir según el tipo de admin
      const userRole = response.user?.role;
      if (userRole === 'superadmin') {
        navigate('/admin/dashboard');
      } else if (userRole === 'admin') {
        navigate('/admin');
      } else {
        // Si no es admin, cerrar sesión y mostrar error
        await logout();
        throw new Error('Este usuario no tiene permisos administrativos. Use el login regular.');
      }
    } catch (err) {
      logger.error('Admin login error:', err);
      setError(err.message || 'Error en el inicio de sesión administrativo');
    } finally {
      setIsLoading(false);
    }
  };

  const fillCredentials = (email) => {
    let password;
    
    if (email === 'superadmin@voicebio.com') {
      password = 'SuperAdmin2024!';
    } else if (email === 'admin@test.com') {
      password = '123456';
    } else {
      password = 'AdminEmpresa2024!';
    }
    
    setFormData({
      email,
      password
    });
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-red-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-orange-400/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-yellow-400/20 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      <div className="relative z-10 min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="mx-auto h-16 w-16 bg-gradient-to-br from-red-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-xl mb-4">
              <Shield className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
              Acceso Administrativo
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
              Panel de administración - Solo personal autorizado
            </p>
          </div>

          <Card variant="glass" className="p-8 shadow-2xl backdrop-blur-xl bg-white dark:bg-gray-900/80 border border-red-200/40">
            {/* Admin Credentials Helper */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Credenciales de Administrador:</h3>
              <div className="space-y-2">
                {adminCredentials.map((cred, index) => (
                  <button
                    key={index}
                    onClick={() => fillCredentials(cred.email)}
                    className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-red-300 hover:bg-red-50/50 transition-all duration-200 group"
                  >
                    <div className="text-xs font-medium text-red-600">{cred.role}</div>
                    <div className="text-sm text-gray-700 group-hover:text-red-700">{cred.email}</div>
                  </button>
                ))}
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50/80 border border-red-200 rounded-lg p-4 flex items-center space-x-3">
                  <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                  <span className="text-sm text-red-700">{error}</span>
                </div>
              )}

              <div>
                <label htmlFor="email" className="block text-sm font-semibold text-gray-700 mb-3">
                  Email Administrativo
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-red-400" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="username"
                    required
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-4 py-3 border border-red-200/60 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent backdrop-blur-sm bg-white dark:bg-gray-900/70 transition-all duration-300"
                    placeholder="admin@empresa.com"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-3">
                  Contraseña Administrativa
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-red-400" />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={formData.password}
                    onChange={handleInputChange}
                    className="w-full pl-10 pr-12 py-3 border border-red-200/60 rounded-xl focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent backdrop-blur-sm bg-white dark:bg-gray-900/70 transition-all duration-300"
                    placeholder="••••••••"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-red-400 hover:text-red-600 transition-colors"
                  >
                    {showPassword ? <EyeOff /> : <Eye />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full bg-gradient-to-r from-red-500 to-orange-600 hover:from-red-600 hover:to-orange-700 text-white font-semibold py-3 px-6 rounded-xl shadow-lg transform transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Verificando credenciales...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <Shield className="h-5 w-5 mr-2" />
                    Acceder al Panel Administrativo
                  </div>
                )}
              </Button>
            </form>

            <div className="mt-8 pt-6 border-t border-red-200/40">
              <div className="text-center">
                <Link 
                  to="/login" 
                  className="text-sm font-medium text-red-600 hover:text-red-700 transition-colors duration-200 flex items-center justify-center"
                >
                  <User className="h-4 w-4 mr-1" />
                  ¿Eres usuario regular? Inicia sesión aquí
                </Link>
              </div>
            </div>

            {/* Security Notice */}
            <div className="mt-4 p-3 bg-amber-50/80 border border-amber-200/60 rounded-lg">
              <div className="flex items-start space-x-2">
                <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-700">
                  <strong>Aviso de Seguridad:</strong> Este es un panel de administración restringido. 
                  Solo personal autorizado puede acceder. Todos los accesos quedan registrados.
                </p>
              </div>
            </div>
          </Card>

          <div className="mt-6 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              VoiceAuth Admin Panel • Versión 1.0.0 • {new Date().getFullYear()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
