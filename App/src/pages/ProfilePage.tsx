import { useState, useEffect } from 'react';
import {
  User,
  Mail,
  Building,
  Save,
  Loader2,
  Lock,
  Eye,
  EyeOff,
  Shield,
  Calendar,
  Key,
  CheckCircle,
  XCircle,
  Activity,
  LogIn,
  Edit,
} from 'lucide-react';
import MainLayout from '../components/ui/MainLayout';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/apiServices';
import toast from 'react-hot-toast';

const ProfilePage = () => {
  const { user, refreshUser } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordSection, setShowPasswordSection] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    company: '',
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    if (user) {
      setFormData({
        firstName: user.first_name || '',
        lastName: user.last_name || '',
        email: user.email || '',
        company: user.company || '',
      });
    }
  }, [user]);

  // Helper function to get user initials
  const getInitials = (name?: string) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  // Password strength calculator
  const calculatePasswordStrength = (password: string) => {
    let strength = 0;
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[^A-Za-z0-9]/.test(password),
    };

    if (checks.length) strength += 20;
    if (checks.uppercase) strength += 20;
    if (checks.lowercase) strength += 20;
    if (checks.number) strength += 20;
    if (checks.special) strength += 20;

    return { strength, checks };
  };

  const getStrengthLabel = (strength: number) => {
    if (strength < 40) return { label: 'Débil', color: 'bg-red-500' };
    if (strength < 80) return { label: 'Media', color: 'bg-yellow-500' };
    return { label: 'Fuerte', color: 'bg-green-500' };
  };

  const passwordStrength = calculatePasswordStrength(passwordData.newPassword);
  const strengthInfo = getStrengthLabel(passwordStrength.strength);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const updateData = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        company: formData.company,
      };

      const response = await authService.updateProfile(updateData);

      if (response.success) {
        toast.success('Perfil actualizado exitosamente');
        setIsEditing(false);
        if (refreshUser) {
          await refreshUser();
        } else {
          window.location.reload();
        }
      } else {
        toast.error(
          (response as any).error || (response as any).message || 'Error al actualizar perfil'
        );
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      toast.error('Ocurrió un error inesperado');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toast.error('Las contraseñas no coinciden');
      return;
    }

    if (passwordData.newPassword.length < 8) {
      toast.error('La contraseña debe tener al menos 8 caracteres');
      return;
    }

    setIsLoading(true);
    try {
      const response = await authService.changePassword(
        passwordData.currentPassword,
        passwordData.newPassword
      );

      if (response.success) {
        toast.success('Contraseña actualizada exitosamente');
        setPasswordData({
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        });
        setShowPasswordSection(false);
      } else {
        toast.error(response.error || 'Error al cambiar la contraseña');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      toast.error('Error al cambiar la contraseña');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent mb-2">
          Mi Perfil
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Gestiona tu información personal y seguridad
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Avatar & Personal Information */}
          <Card className="hover:shadow-xl transition-shadow duration-300">
            <div className="p-6">
              {/* Avatar Section */}
              <div className="flex flex-col items-center mb-8">
                <div className="relative group">
                  <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center text-white text-3xl font-bold shadow-lg ring-4 ring-white dark:ring-gray-900 transition-transform duration-300 group-hover:scale-105">
                    {getInitials(user?.name || `${user?.first_name} ${user?.last_name}`)}
                  </div>
                  <div className="absolute bottom-0 right-0 w-6 h-6 bg-green-500 rounded-full border-4 border-white dark:border-gray-900 animate-pulse" />
                </div>
                <h2 className="mt-4 text-2xl font-bold text-gray-800 dark:text-gray-200">
                  {user?.name || `${user?.first_name} ${user?.last_name}` || 'Usuario'}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email}</p>
              </div>

              {/* Personal Info Form */}
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center">
                  <div className="p-3 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900 dark:to-indigo-900 rounded-xl mr-4">
                    <User className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200">
                      Información Personal
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Actualiza tus datos personales
                    </p>
                  </div>
                </div>
                <Button
                  variant={isEditing ? 'ghost' : 'outline'}
                  onClick={() => setIsEditing(!isEditing)}
                  className="transition-all duration-200 hover:scale-105"
                >
                  {isEditing ? 'Cancelar' : (
                    <>
                      <Edit className="h-4 w-4 mr-2" />
                      Editar
                    </>
                  )}
                </Button>
              </div>

              <form onSubmit={handleSubmit}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Nombre
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        name="firstName"
                        value={formData.firstName}
                        onChange={handleChange}
                        disabled={!isEditing}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-60 disabled:bg-gray-50 dark:disabled:bg-gray-900 transition-all duration-200 focus:shadow-lg"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Apellido
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        name="lastName"
                        value={formData.lastName}
                        onChange={handleChange}
                        disabled={!isEditing}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-60 disabled:bg-gray-50 dark:disabled:bg-gray-900 transition-all duration-200 focus:shadow-lg"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="email"
                        name="email"
                        value={formData.email}
                        disabled={true}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      El email no se puede cambiar directamente
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Empresa
                    </label>
                    <div className="relative">
                      <Building className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        name="company"
                        value={formData.company}
                        onChange={handleChange}
                        disabled={!isEditing}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-60 disabled:bg-gray-50 dark:disabled:bg-gray-900 transition-all duration-200 focus:shadow-lg"
                      />
                    </div>
                  </div>
                </div>

                {isEditing && (
                  <div className="flex justify-end">
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="transition-all duration-200 hover:scale-105"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Guardando...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" />
                          Guardar Cambios
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </form>
            </div>
          </Card>

          {/* Password Section */}
          <Card className="hover:shadow-xl transition-shadow duration-300">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="p-3 bg-gradient-to-br from-red-100 to-orange-100 dark:from-red-900 dark:to-orange-900 rounded-xl mr-4">
                    <Lock className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200">
                      Seguridad
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Cambia tu contraseña
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordSection(!showPasswordSection)}
                  className="transition-all duration-200 hover:scale-105"
                >
                  {showPasswordSection ? 'Cancelar' : 'Cambiar Contraseña'}
                </Button>
              </div>

              {showPasswordSection && (
                <form onSubmit={handlePasswordSubmit} className="space-y-4 animate-in slide-in-from-top duration-300">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Contraseña Actual
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type={showCurrentPassword ? 'text' : 'password'}
                        name="currentPassword"
                        value={passwordData.currentPassword}
                        onChange={handlePasswordChange}
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 focus:shadow-lg"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      >
                        {showCurrentPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Nueva Contraseña
                    </label>
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type={showNewPassword ? 'text' : 'password'}
                        name="newPassword"
                        value={passwordData.newPassword}
                        onChange={handlePasswordChange}
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 focus:shadow-lg"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      >
                        {showNewPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>

                    {/* Password Strength Indicator */}
                    {passwordData.newPassword && (
                      <div className="mt-3 space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">
                            Fortaleza:
                          </span>
                          <span className={`font-medium ${
                            passwordStrength.strength < 40
                              ? 'text-red-600'
                              : passwordStrength.strength < 80
                              ? 'text-yellow-600'
                              : 'text-green-600'
                          }`}>
                            {strengthInfo.label}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full ${strengthInfo.color} transition-all duration-300`}
                            style={{ width: `${passwordStrength.strength}%` }}
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className={`flex items-center ${passwordStrength.checks.length ? 'text-green-600' : 'text-gray-400'}`}>
                            {passwordStrength.checks.length ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            8+ caracteres
                          </div>
                          <div className={`flex items-center ${passwordStrength.checks.uppercase ? 'text-green-600' : 'text-gray-400'}`}>
                            {passwordStrength.checks.uppercase ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            Mayúscula
                          </div>
                          <div className={`flex items-center ${passwordStrength.checks.lowercase ? 'text-green-600' : 'text-gray-400'}`}>
                            {passwordStrength.checks.lowercase ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            Minúscula
                          </div>
                          <div className={`flex items-center ${passwordStrength.checks.number ? 'text-green-600' : 'text-gray-400'}`}>
                            {passwordStrength.checks.number ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            Número
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Confirmar Nueva Contraseña
                    </label>
                    <div className="relative">
                      <Key className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        name="confirmPassword"
                        value={passwordData.confirmPassword}
                        onChange={handlePasswordChange}
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 focus:shadow-lg"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                    {passwordData.confirmPassword && passwordData.newPassword !== passwordData.confirmPassword && (
                      <p className="text-xs text-red-600 mt-1 flex items-center">
                        <XCircle className="h-3 w-3 mr-1" />
                        Las contraseñas no coinciden
                      </p>
                    )}
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="transition-all duration-200 hover:scale-105"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Actualizando...
                        </>
                      ) : (
                        <>
                          <Shield className="mr-2 h-4 w-4" />
                          Actualizar Contraseña
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              )}
            </div>
          </Card>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
          {/* Voice Profile Status */}
          <Card className="hover:shadow-xl transition-shadow duration-300">
            <div className="p-6">
              <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <Shield className="h-5 w-5 mr-2 text-blue-600 dark:text-blue-400" />
                Perfil de Voz
              </h3>
              <div
                className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                  user?.voice_template
                    ? 'bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200 dark:border-green-800'
                    : 'bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 border-orange-200 dark:border-orange-800'
                }`}
              >
                <p
                  className={`text-sm font-medium mb-2 ${
                    user?.voice_template
                      ? 'text-green-700 dark:text-green-400'
                      : 'text-orange-700 dark:text-orange-400'
                  }`}
                >
                  {user?.voice_template ? '✓ Perfil Activo' : '⚠ Sin Configurar'}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {user?.voice_template
                    ? 'Tu perfil de voz está configurado y listo para usar'
                    : 'Configura tu perfil de voz para usar la verificación biométrica'}
                </p>
              </div>
            </div>
          </Card>

          {/* Account Info */}
          <Card className="hover:shadow-xl transition-shadow duration-300">
            <div className="p-6">
              <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <User className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" />
                Información de Cuenta
              </h3>
              <div className="space-y-4">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg transition-colors duration-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Rol</p>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200 capitalize">
                    {user?.role || 'Usuario'}
                  </p>
                </div>
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg transition-colors duration-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center">
                    <Calendar className="h-3 w-3 mr-1" />
                    Miembro desde
                  </p>
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {user?.created_at
                      ? new Date(user.created_at).toLocaleDateString('es-ES', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Recent Activity */}
          <Card className="hover:shadow-xl transition-shadow duration-300">
            <div className="p-6">
              <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <Activity className="h-5 w-5 mr-2 text-indigo-600 dark:text-indigo-400" />
                Actividad Reciente
              </h3>
              <div className="space-y-3">
                <div className="flex items-start p-3 bg-gray-50 dark:bg-gray-800 rounded-lg transition-colors duration-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                  <LogIn className="h-4 w-4 mr-3 mt-0.5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800 dark:text-gray-200">
                      Último acceso
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Hoy a las {new Date().toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
                {user?.voice_template && (
                  <div className="flex items-start p-3 bg-gray-50 dark:bg-gray-800 rounded-lg transition-colors duration-200 hover:bg-gray-100 dark:hover:bg-gray-700">
                    <Shield className="h-4 w-4 mr-3 mt-0.5 text-green-600 dark:text-green-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 dark:text-gray-200">
                        Perfil de voz activo
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Configurado correctamente
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </MainLayout>
  );
};

export default ProfilePage;
