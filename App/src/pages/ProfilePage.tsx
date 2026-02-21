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
  Edit,
  UserCircle,
  CreditCard,
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
    rut: '',
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    if (user) {
      const formattedUser = {
        ...user,
        first_name: user?.first_name || user?.name?.split(' ')[0] || '',
        last_name: user?.last_name || user?.name?.split(' ').slice(1).join(' ') || '',
      };
      setFormData({
        firstName: formattedUser.first_name || '',
        lastName: formattedUser.last_name || '',
        email: formattedUser.email || '',
        company: formattedUser.company || '',
        rut: formattedUser.rut || '',
      });
    }
  }, [user]);

  const getInitials = (name?: string) => {
    if (!name) return 'U';
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return `${parts[0]?.[0] || ''}${parts[1]?.[0] || ''}`.toUpperCase();
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

  // Función para validar RUT chileno
  const validateRUT = (rut: string): boolean => {
    if (!rut) return true; // RUT vacío es válido (opcional)

    // Limpiar el RUT (remover puntos y guión)
    const cleanRut = rut.replace(/\./g, '').replace(/-/g, '');

    // Validar formato básico (mínimo 8 caracteres)
    if (cleanRut.length < 8) return false;

    // Separar número y dígito verificador
    const rutNumber = cleanRut.slice(0, -1);
    const verifier = cleanRut.slice(-1).toUpperCase();

    // Validar que el número sea numérico
    if (!/^\d+$/.test(rutNumber)) return false;

    // Calcular dígito verificador
    let sum = 0;
    let multiplier = 2;

    for (let i = rutNumber.length - 1; i >= 0; i--) {
      sum += parseInt(rutNumber[i]) * multiplier;
      multiplier = multiplier === 7 ? 2 : multiplier + 1;
    }

    const expectedVerifier = 11 - (sum % 11);
    const calculatedVerifier =
      expectedVerifier === 11 ? '0' : expectedVerifier === 10 ? 'K' : expectedVerifier.toString();

    return verifier === calculatedVerifier;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validar RUT si fue proporcionado
    if (formData.rut && !validateRUT(formData.rut)) {
      toast.error('RUT inválido. Formato: 12345678-9');
      return;
    }

    setIsLoading(true);

    try {
      const updateData: any = {
        first_name: formData.firstName,
        last_name: formData.lastName,
        company: formData.company,
      };

      // Solo enviar RUT si tiene valor
      if (formData.rut) {
        updateData.rut = formData.rut;
      }

      const response = await authService.updateProfile(updateData);

      if (response.success) {
        toast.success('Perfil actualizado exitosamente');
        setIsEditing(false);

        // Refresh user data
        if (refreshUser) {
          await refreshUser();
        } else {
          window.location.reload();
        }
      } else {
        toast.error(
          (response as { error?: string; message?: string }).error ||
            (response as { error?: string; message?: string }).message ||
            'Error al actualizar perfil'
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
        <h1 className="text-4xl font-bold bg-linear-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent mb-2">
          Mi Perfil
        </h1>
        <p className="text-lg text-gray-700 dark:text-gray-300">
          Gestiona tu información personal y configuración de cuenta
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Information Card */}
          <Card>
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="p-3 bg-linear-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl mr-4">
                    <UserCircle className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">
                      Información Personal
                    </h2>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      Actualiza tus datos personales
                    </p>
                  </div>
                </div>
                <Button
                  variant={isEditing ? 'ghost' : 'outline'}
                  onClick={() => setIsEditing(!isEditing)}
                >
                  {isEditing ? (
                    'Cancelar'
                  ) : (
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
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-60 disabled:bg-gray-50 dark:disabled:bg-gray-900 transition-all"
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
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-60 disabled:bg-gray-50 dark:disabled:bg-gray-900 transition-all"
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
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-300 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                      El email no se puede cambiar
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
                        value={formData.company || 'No especificada'}
                        disabled={true}
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-100 dark:bg-gray-900 text-gray-600 dark:text-gray-300 cursor-not-allowed"
                      />
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                      La empresa no se puede cambiar
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      RUT{' '}
                      {!formData.rut && !user?.rut && (
                        <span className="text-xs text-blue-600">(Opcional)</span>
                      )}
                    </label>
                    <div className="relative">
                      <CreditCard className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                      <input
                        type="text"
                        name="rut"
                        value={formData.rut || ''}
                        onChange={handleChange}
                        disabled={!isEditing}
                        placeholder="12345678-9"
                        className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-60 disabled:bg-gray-50 dark:disabled:bg-gray-900 transition-all"
                      />
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                      {isEditing
                        ? 'Formato: 12345678-9 o 12.345.678-9'
                        : formData.rut
                          ? 'RUT registrado'
                          : 'Sin RUT registrado'}
                    </p>
                  </div>
                </div>

                {isEditing && (
                  <div className="flex justify-end">
                    <Button type="submit" disabled={isLoading}>
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

          {/* Security Card */}
          <Card>
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="p-3 bg-linear-to-br from-red-100 to-orange-100 dark:from-red-900/50 dark:to-orange-900/50 rounded-xl mr-4">
                    <Lock className="h-6 w-6 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">
                      Seguridad
                    </h2>
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      Gestiona tu contraseña
                    </p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={() => setShowPasswordSection(!showPasswordSection)}
                >
                  {showPasswordSection ? 'Cancelar' : 'Cambiar Contraseña'}
                </Button>
              </div>

              {showPasswordSection && (
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
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
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
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
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowNewPassword(!showNewPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
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
                          <span className="text-gray-700 dark:text-gray-300">Fortaleza:</span>
                          <span
                            className={`font-medium ${
                              passwordStrength.strength < 40
                                ? 'text-red-600'
                                : passwordStrength.strength < 80
                                  ? 'text-yellow-600'
                                  : 'text-green-600'
                            }`}
                          >
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
                          <div
                            className={`flex items-center ${passwordStrength.checks.length ? 'text-green-600' : 'text-gray-400'}`}
                          >
                            {passwordStrength.checks.length ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            8+ caracteres
                          </div>
                          <div
                            className={`flex items-center ${passwordStrength.checks.uppercase ? 'text-green-600' : 'text-gray-400'}`}
                          >
                            {passwordStrength.checks.uppercase ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            Mayúscula
                          </div>
                          <div
                            className={`flex items-center ${passwordStrength.checks.lowercase ? 'text-green-600' : 'text-gray-400'}`}
                          >
                            {passwordStrength.checks.lowercase ? (
                              <CheckCircle className="h-3 w-3 mr-1" />
                            ) : (
                              <XCircle className="h-3 w-3 mr-1" />
                            )}
                            Minúscula
                          </div>
                          <div
                            className={`flex items-center ${passwordStrength.checks.number ? 'text-green-600' : 'text-gray-400'}`}
                          >
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
                        className="w-full pl-10 pr-12 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-5 w-5" />
                        ) : (
                          <Eye className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                    {passwordData.confirmPassword &&
                      passwordData.newPassword !== passwordData.confirmPassword && (
                        <p className="text-xs text-red-600 mt-1 flex items-center">
                          <XCircle className="h-3 w-3 mr-1" />
                          Las contraseñas no coinciden
                        </p>
                      )}
                  </div>

                  <div className="flex justify-end pt-4">
                    <Button type="submit" disabled={isLoading}>
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

        {/* Sidebar */}
        <div className="space-y-6">
          {/* User Avatar Card */}
          <Card>
            <div className="p-6">
              <div className="flex flex-col items-center text-center">
                <div className="w-24 h-24 rounded-full bg-linear-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center text-white text-3xl font-bold shadow-lg mb-4">
                  {getInitials(user?.name || `${user?.first_name} ${user?.last_name}`)}
                </div>
                <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-1">
                  {user?.name || `${user?.first_name} ${user?.last_name}` || 'Usuario'}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{user?.email}</p>
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300 capitalize">
                  {user?.role || 'Usuario'}
                </span>
              </div>
            </div>
          </Card>

          {/* Account Info Card */}
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center">
                <Calendar className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" />
                Información de Cuenta
              </h3>
              <div className="space-y-3">
                <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">Miembro desde</p>
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
                {user?.company && (
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p className="text-xs text-gray-600 dark:text-gray-300 mb-1">Empresa</p>
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                      {user.company}
                    </p>
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
