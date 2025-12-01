import { useState } from 'react';
import {
  User,
  Shield,
  Bell,
  Palette,
  Save,
  Eye,
  EyeOff,
  Mic,
  Clock,
  Mail,
  Smartphone,
  AlertTriangle,
  Download,
  Globe,
  ChevronDown,
} from 'lucide-react';
import Modal from './Modal';
import Button from './Button';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';
import { authService } from '../../services/apiServices';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal = ({ isOpen, onClose }: SettingsModalProps) => {
  const { user } = useAuth();
  const { setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Estados del formulario
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    securityAlerts: true,
    systemUpdates: false,
  });

  const [securitySettings, setSecuritySettings] = useState({
    twoFactorAuth: false,
    biometricVerification: true,
    sessionTimeout: 30,
    loginNotifications: true,
  });

  const [appearance, setAppearance] = useState(() => {
    try {
      const keys = Object.keys(localStorage);
      const themeKey = keys.find((key) => key.includes('theme'));

      if (themeKey) {
        const saved = localStorage.getItem(themeKey);

        if (saved) {
          const parsed = JSON.parse(saved);
          const themeValue = parsed === 'auto' ? 'light' : parsed;

          if (themeValue !== 'light' && themeValue !== 'dark' && themeValue !== 'auto') {
            return {
              theme: 'light',
              language: 'es',
              fontSize: 'medium',
            };
          }

          return {
            theme: themeValue,
            language: 'es',
            fontSize: 'medium',
          };
        }
      }
    } catch (error) {
      console.error('Error loading theme preference:', error);
    }

    return {
      theme: 'light',
      language: 'es',
      fontSize: 'medium',
    };
  });

  const handleSave = async (section: string) => {
    setIsLoading(true);
    try {
      // Si es la sección de apariencia, aplicar el tema
      if (section === 'appearance') {
        setTheme(appearance.theme as 'light' | 'dark');
      }

      let updateData = {};
      
      if (section === 'profile') {
        updateData = {
          name: profileData.name,
          email: profileData.email,
          // Password change should be a separate endpoint ideally, but we'll skip it for now or add it later
        };
        // If password fields are filled, we might want to handle it (requires backend support for password change)
      } else if (section === 'notifications') {
        updateData = {
          settings: {
            ...user?.settings,
            notifications: notificationSettings
          }
        };
      } else if (section === 'security') {
        updateData = {
          settings: {
            ...user?.settings,
            security: securitySettings
          }
        };
      } else if (section === 'appearance') {
        updateData = {
          settings: {
            ...user?.settings,
            appearance: appearance
          }
        };
      }

      const response = await authService.updateProfile(updateData);
      
      if (response.success) {
        console.log(`Guardando configuración de ${section}`);
        // Optionally show success toast here if not handled globally
      } else {
        console.error('Error updating profile settings');
      }

    } catch (error) {
      console.error('Error al guardar:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Estilos para inputs mejorados
  const inputClassName = `
    w-full px-6 py-4 rounded-2xl transition-all duration-300
    bg-linear-to-r from-white/90 to-white/70 dark:from-gray-700/90 dark:to-gray-800/70 backdrop-blur-md border border-gray-200 dark:border-gray-700/50 dark:border-gray-600/50
    focus:ring-4 focus:ring-blue-300/30 dark:focus:ring-blue-500/30 focus:border-blue-400 dark:focus:border-blue-500 focus:bg-linear-to-r focus:from-white/95 focus:to-white/80 dark:focus:from-gray-700/95 dark:focus:to-gray-800/80
    hover:bg-linear-to-r hover:from-white/95 hover:to-white/80 dark:hover:from-gray-700/95 dark:hover:to-gray-800/80 hover:border-gray-300/60 dark:hover:border-gray-600/60 hover:shadow-xl
    placeholder:text-gray-500 dark:text-gray-400 dark:placeholder:text-gray-400 text-gray-800 dark:text-gray-100 font-medium text-lg
    shadow-xl
  `;

  const selectClassName = inputClassName;

  const renderProfileTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto pr-2">
      <div>
        <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-3">
            <User className="h-4 w-4 text-white" />
          </div>
          Información Personal
        </h3>
        <div className="p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
          <div className="grid grid-cols-1 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
                Nombre Completo
              </label>
              <input
                type="text"
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                className={inputClassName}
                placeholder="Tu nombre completo"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
                Email
              </label>
              <input
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                className={inputClassName}
                placeholder="tu@email.com"
              />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-green-500 to-emerald-600 flex items-center justify-center mr-3">
            <Shield className="h-4 w-4 text-white" />
          </div>
          Cambiar Contraseña
        </h3>
        <div className="space-y-6">
          <div className="p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
              Contraseña Actual
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={profileData.currentPassword}
                onChange={(e) =>
                  setProfileData({ ...profileData, currentPassword: e.target.value })
                }
                className={`${inputClassName} pr-12`}
                placeholder="Tu contraseña actual"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-4 flex items-center hover:bg-gray-100/50 dark:hover:bg-gray-700/50 rounded-r-xl"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                )}
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
                Nueva Contraseña
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={profileData.newPassword}
                onChange={(e) => setProfileData({ ...profileData, newPassword: e.target.value })}
                className={inputClassName}
                placeholder="Nueva contraseña"
              />
            </div>
            <div className="p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">
                Confirmar Contraseña
              </label>
              <input
                type={showPassword ? 'text' : 'password'}
                value={profileData.confirmPassword}
                onChange={(e) =>
                  setProfileData({ ...profileData, confirmPassword: e.target.value })
                }
                className={inputClassName}
                placeholder="Confirma tu contraseña"
              />
            </div>
          </div>
        </div>
      </div>

      <Button
        onClick={() => handleSave('profile')}
        disabled={isLoading}
        className="w-full md:w-auto bg-linear-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl px-8 py-3"
      >
        <Save className="h-4 w-4 mr-2" />
        {isLoading ? 'Guardando...' : 'Guardar Cambios'}
      </Button>
    </div>
  );

  const renderSecurityTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto pr-2">
      <div>
        <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-red-500 to-pink-600 flex items-center justify-center mr-3">
            <Shield className="h-4 w-4 text-white" />
          </div>
          Configuración de Seguridad
        </h3>
        <div className="space-y-6">
          {/* Toggle mejorado para 2FA */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-purple-500 to-indigo-600 flex items-center justify-center mr-4">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Autenticación de Dos Factores
                </h4>
                <p className="text-sm text-gray-600 dark:text-blue-400/70">
                  Añade una capa extra de seguridad a tu cuenta
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={securitySettings.twoFactorAuth}
                onChange={(e) =>
                  setSecuritySettings({ ...securitySettings, twoFactorAuth: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-linear-to-r peer-checked:from-blue-500 peer-checked:to-indigo-600 shadow-lg"></div>
            </label>
          </div>

          {/* Selector de tiempo de sesión mejorado */}
          <div className="p-6 rounded-2xl transition-all duration-300 hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
                <Clock className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">Tiempo de Sesión</h4>
                <p className="text-sm text-gray-600 dark:text-blue-400/70">
                  Duración antes del cierre automático
                </p>
              </div>
            </div>
            <div className="relative">
              <select
                value={securitySettings.sessionTimeout}
                onChange={(e) =>
                  setSecuritySettings({
                    ...securitySettings,
                    sessionTimeout: parseInt(e.target.value),
                  })
                }
                className="w-full px-6 py-4 bg-linear-to-r from-white/90 to-white/70 dark:from-gray-700/90 dark:to-gray-800/70 backdrop-blur-md border border-blue-200/50 dark:border-gray-600/50 rounded-2xl focus:ring-4 focus:ring-blue-300/30 dark:focus:ring-blue-500/30 focus:border-blue-400 dark:focus:border-blue-500 shadow-xl text-gray-800 dark:text-gray-100 font-semibold text-lg appearance-none cursor-pointer hover:bg-linear-to-r hover:from-white/95 hover:to-white/80 dark:hover:from-gray-700/95 dark:hover:to-gray-800/80 hover:shadow-2xl pr-14"
              >
                <option value={15}>⏱️ 15 minutos</option>
                <option value={30}>⏰ 30 minutos</option>
                <option value={60}>🕐 1 hora</option>
                <option value={120}>🕑 2 horas</option>
              </select>
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-6 w-6 text-blue-500 dark:text-blue-400" />
              </div>
            </div>
          </div>

          {/* Toggle para notificaciones de login */}
          <div className="flex items-center justify-between p-6 rounded-2xl transition-all duration-300 hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-amber-500 to-orange-600 flex items-center justify-center mr-4">
                <Bell className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Notificaciones de Inicio de Sesión
                </h4>
                <p className="text-sm text-gray-600 dark:text-blue-400/70">
                  Recibir alertas cuando alguien acceda a tu cuenta
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={securitySettings.loginNotifications}
                onChange={(e) =>
                  setSecuritySettings({ ...securitySettings, loginNotifications: e.target.checked })
                }
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-amber-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-linear-to-r peer-checked:from-amber-500 peer-checked:to-orange-600 shadow-lg"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationsTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto overflow-x-hidden">
      <div>
        <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-blue-500 to-purple-600 flex items-center justify-center mr-3">
            <Bell className="h-4 w-4 text-white" />
          </div>
          Preferencias de Notificación
        </h3>
        <div className="space-y-6">
          {/* Email Notifications */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-4">
                <Mail className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Notificaciones por Email
                </h4>
                <p className="text-sm text-gray-600 dark:text-blue-400/70">
                  Recibir notificaciones importantes por correo
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.emailNotifications}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    emailNotifications: e.target.checked,
                  })
                }
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-linear-to-r peer-checked:from-emerald-500 peer-checked:to-blue-600 shadow-lg"></div>
            </label>
          </div>

          {/* Push Notifications */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-4">
                <Smartphone className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Notificaciones Push
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Notificaciones en tiempo real en el navegador
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.pushNotifications}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    pushNotifications: e.target.checked,
                  })
                }
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-linear-to-r peer-checked:from-blue-500 peer-checked:to-indigo-600 shadow-lg"></div>
            </label>
          </div>

          {/* Security Alerts */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-red-500 to-orange-600 flex items-center justify-center mr-4">
                <AlertTriangle className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Alertas de Seguridad
                </h4>
                <p className="text-sm text-gray-600 dark:text-blue-400/70">
                  Notificaciones sobre actividad sospechosa
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.securityAlerts}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    securityAlerts: e.target.checked,
                  })
                }
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-linear-to-r peer-checked:from-red-500 peer-checked:to-orange-600 shadow-lg"></div>
            </label>
          </div>

          {/* System Updates */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-purple-500 to-pink-600 flex items-center justify-center mr-4">
                <Download className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Actualizaciones del Sistema
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Información sobre nuevas funciones y actualizaciones
                </p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.systemUpdates}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    systemUpdates: e.target.checked,
                  })
                }
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-linear-to-r peer-checked:from-purple-500 peer-checked:to-pink-600 shadow-lg"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAppearanceTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto overflow-x-hidden">
      <div>
        <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-linear-to-br from-purple-500 to-pink-600 flex items-center justify-center mr-3">
            <Palette className="h-4 w-4 text-white" />
          </div>
          Personalización
        </h3>
        <div className="space-y-6">
          {/* Theme Selector */}
          <div className="p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Palette className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Tema de la Aplicación
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Elige el esquema de colores preferido
                </p>
              </div>
            </div>
            <div className="relative">
              <select
                value={appearance.theme}
                onChange={(e) => {
                  const newTheme = e.target.value as 'light' | 'dark' | 'auto';
                  setAppearance({ ...appearance, theme: newTheme });
                  setTheme(newTheme);
                }}
                className="w-full px-6 py-4 bg-linear-to-r from-white/90 to-white/70 dark:from-gray-700/90 dark:to-gray-800/70 backdrop-blur-md border border-indigo-200/50 dark:border-gray-600/50 rounded-2xl focus:ring-4 focus:ring-indigo-300/30 dark:focus:ring-indigo-500/30 focus:border-indigo-400 dark:focus:border-indigo-500 shadow-xl text-gray-800 dark:text-gray-100 font-semibold text-lg appearance-none cursor-pointer hover:bg-linear-to-r hover:from-white/95 hover:to-white/80 dark:hover:from-gray-700/95 dark:hover:to-gray-800/80 hover:shadow-2xl pr-14"
              >
                <option value="light">🌞 Claro</option>
                <option value="dark">🌙 Oscuro</option>
                <option value="auto">🔄 Automático (Sistema)</option>
              </select>
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-6 w-6 text-indigo-500 dark:text-indigo-400" />
              </div>
            </div>
          </div>

          {/* Language Setting */}
          <div className="p-6 rounded-2xl hover:shadow-lg bg-white dark:bg-gray-800/70 border border-gray-200/60 dark:border-gray-600/40">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 rounded-xl bg-linear-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <Globe className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">
                  Idioma de la Interfaz
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Selecciona tu idioma preferido
                </p>
              </div>
            </div>
            <div className="relative">
              <select
                value={appearance.language}
                onChange={(e) => setAppearance({ ...appearance, language: e.target.value })}
                className="w-full px-6 py-4 bg-linear-to-r from-white/90 to-white/70 dark:from-gray-700/90 dark:to-gray-800/70 backdrop-blur-md border border-emerald-200/50 dark:border-gray-600/50 rounded-2xl focus:ring-4 focus:ring-emerald-300/30 dark:focus:ring-emerald-500/30 focus:border-emerald-400 dark:focus:border-emerald-500 shadow-xl text-gray-800 dark:text-gray-100 font-semibold text-lg appearance-none cursor-pointer hover:bg-linear-to-r hover:from-white/95 hover:to-white/80 dark:hover:from-gray-700/95 dark:hover:to-gray-800/80 hover:shadow-2xl pr-14"
              >
                <option value="es">🇪🇸 Español</option>
                <option value="en">🇺🇸 English</option>
                <option value="pt">🇧🇷 Português</option>
              </select>
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-6 w-6 text-emerald-500 dark:text-emerald-400" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  interface Tab {
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  }

  const tabs: Tab[] = [
    { id: 'profile', label: 'Perfil', icon: User },
    { id: 'security', label: 'Seguridad', icon: Shield },
    { id: 'notifications', label: 'Notificaciones', icon: Bell },
    { id: 'appearance', label: 'Apariencia', icon: Palette },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return renderProfileTab();
      case 'security':
        return renderSecurityTab();
      case 'notifications':
        return renderNotificationsTab();
      case 'appearance':
        return renderAppearanceTab();
      default:
        return renderProfileTab();
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="⚙️ Configuración" size="xl">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar de configuración mejorado */}
        <div className="lg:col-span-1">
          <div className="relative overflow-hidden rounded-2xl p-4 shadow-lg border bg-linear-to-br from-blue-50/80 to-purple-50/80 dark:from-gray-800/70 dark:to-gray-800/70 border-blue-200/40 dark:border-gray-600/40 backdrop-blur-xl">
            {/* Elemento decorativo */}
            <div
              className="absolute top-0 right-0 w-20 h-20 rounded-full opacity-30"
              style={{
                background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                filter: 'blur(20px)',
              }}
            />

            <nav className="relative space-y-3">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      w-full flex items-center px-4 py-3 rounded-xl text-sm font-medium 
                      transition-all duration-300 relative overflow-hidden group
                      ${
                        activeTab === tab.id
                          ? 'bg-linear-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-[1.02]'
                          : 'text-gray-700 dark:text-blue-400/70 hover:bg-white dark:hover:bg-gray-700/60 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-md hover:scale-[1.01]'
                      }
                    `}
                  >
                    {/* Efecto de brillo en hover */}
                    <div className="absolute inset-0 bg-linear-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transform -translate-x-full group-hover:translate-x-full transition-all duration-700" />

                    <Icon className="h-5 w-5 mr-3 relative z-10" />
                    <span className="relative z-10">{tab.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Contenido principal mejorado */}
        <div className="lg:col-span-3">
          <div className="relative overflow-hidden rounded-2xl p-8 shadow-lg border min-h-96 bg-white/90 dark:bg-gray-800/70 border-gray-200/60 dark:border-gray-600/40 backdrop-blur-xl">
            {/* Elementos decorativos de fondo */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div
                className="absolute -top-20 -right-20 w-40 h-40 rounded-full opacity-10"
                style={{
                  background: 'linear-gradient(135deg, #06B6D4, #3B82F6)',
                  filter: 'blur(30px)',
                }}
              />
              <div
                className="absolute -bottom-20 -left-20 w-40 h-40 rounded-full opacity-10"
                style={{
                  background: 'linear-gradient(135deg, #8B5CF6, #3B82F6)',
                  filter: 'blur(30px)',
                }}
              />
            </div>

            <div className="relative z-10">{renderTabContent()}</div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default SettingsModal;
