import { useState, useEffect } from 'react';
import { Bell, Shield, Palette, Moon, Sun, Monitor } from 'lucide-react';
import MainLayout from '../components/ui/MainLayout';
import Card from '../components/ui/Card';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/apiServices';
import toast from 'react-hot-toast';

const SettingsPage = () => {
  const { user } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  const [localSettings, setLocalSettings] = useState({
    notifications: {
      email: true,
      push: false,
      verificationAlerts: true,
    },
    security: {
      twoFactor: false,
      sessionTimeout: 30,
      requireReauth: false,
    },
    appearance: {
      theme: 'system',
      language: 'es',
    },
  });

  // Load settings from user profile on mount
  useEffect(() => {
    if (user?.settings) {
      setLocalSettings((prev) => ({
        notifications: {
          ...prev.notifications,
          ...(user?.settings?.notifications || {}),
        },
        security: {
          ...prev.security,
          ...(user?.settings?.security || {}),
        },
        appearance: {
          ...prev.appearance,
          ...(user?.settings?.appearance || {}),
        },
      }));
    }
  }, [user]);

  // Apply theme when it changes
  useEffect(() => {
    const theme = localSettings.appearance.theme;
    const root = window.document.documentElement;

    if (theme === 'dark') {
      root.classList.add('dark');
    } else if (theme === 'light') {
      root.classList.remove('dark');
    } else {
      // System preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (prefersDark) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [localSettings.appearance.theme]);

  // Auto-save settings when they change
  useEffect(() => {
    const saveSettings = async () => {
      // Skip initial load
      if (!user?.settings) return;

      setIsSaving(true);
      try {
        const updateData = {
          settings: localSettings,
        };

        await authService.updateProfile(updateData);
        toast.success('Configuración guardada', { duration: 2000 });
      } catch (error) {
        console.error('Error saving settings:', error);
        toast.error('Error al guardar');
      } finally {
        setIsSaving(false);
      }
    };

    // Debounce to avoid too many saves
    const timeoutId = setTimeout(saveSettings, 1000);
    return () => clearTimeout(timeoutId);
  }, [localSettings, user?.settings]);

  const handleThemeChange = (theme: string) => {
    setLocalSettings((prev) => ({
      ...prev,
      appearance: { ...prev.appearance, theme },
    }));
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent mb-2">
          Configuración
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          Personaliza tu experiencia en VoiceAuth
          {isSaving && (
            <span className="ml-2 text-sm text-blue-600 dark:text-blue-400">• Guardando...</span>
          )}
        </p>
      </div>

      <div className="space-y-6">
        {/* Notifications */}
        <Card>
          <div className="p-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-gradient-to-br from-blue-100 to-indigo-100 dark:from-blue-900/50 dark:to-indigo-900/50 rounded-xl mr-4">
                <Bell className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">
                  Notificaciones
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Gestiona cómo y cuándo recibes notificaciones
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <label className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-xl cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <div>
                  <p className="font-medium text-gray-800 dark:text-gray-200">
                    Notificaciones por Email
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Recibe actualizaciones importantes por correo
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={localSettings.notifications.email}
                  onChange={(e) =>
                    setLocalSettings((prev) => ({
                      ...prev,
                      notifications: { ...prev.notifications, email: e.target.checked },
                    }))
                  }
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
              </label>

              <label className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-xl cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                <div>
                  <p className="font-medium text-gray-800 dark:text-gray-200">
                    Alertas de Verificación
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Notificaciones sobre intentos de verificación
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={localSettings.notifications.verificationAlerts}
                  onChange={(e) =>
                    setLocalSettings((prev) => ({
                      ...prev,
                      notifications: {
                        ...prev.notifications,
                        verificationAlerts: e.target.checked,
                      },
                    }))
                  }
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
              </label>
            </div>
          </div>
        </Card>

        {/* Security */}
        <Card>
          <div className="p-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-gradient-to-br from-green-100 to-emerald-100 dark:from-green-900/50 dark:to-emerald-900/50 rounded-xl mr-4">
                <Shield className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">Seguridad</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Configura las opciones de seguridad de tu cuenta
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                <label className="block mb-3">
                  <p className="font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Tiempo de Sesión
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    Cierra sesión automáticamente después de inactividad
                  </p>
                </label>
                <div className="relative">
                  <select
                    value={localSettings.security.sessionTimeout}
                    onChange={(e) =>
                      setLocalSettings((prev) => ({
                        ...prev,
                        security: { ...prev.security, sessionTimeout: parseInt(e.target.value) },
                      }))
                    }
                    className="w-full px-4 py-3 pr-10 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all appearance-none cursor-pointer hover:border-gray-400 dark:hover:border-gray-500"
                  >
                    <option value={10}>10 minutos</option>
                    <option value={30}>30 minutos</option>
                    <option value={60}>1 hora</option>
                    <option value={120}>2 horas</option>
                    <option value={300}>5 horas</option>
                    <option value={480}>8 horas</option>
                    <option value={1440}>24 horas</option>
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-500 dark:text-gray-400">
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Appearance */}
        <Card>
          <div className="p-6">
            <div className="flex items-center mb-6">
              <div className="p-3 bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900/50 dark:to-pink-900/50 rounded-xl mr-4">
                <Palette className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200">Apariencia</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Personaliza el tema y la apariencia
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <p className="font-medium text-gray-800 dark:text-gray-200 mb-3">Tema de Color</p>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    onClick={() => handleThemeChange('light')}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      localSettings.appearance.theme === 'light'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                    }`}
                  >
                    <Sun className="h-6 w-6 mx-auto mb-2 text-yellow-500" />
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Claro</p>
                  </button>

                  <button
                    onClick={() => handleThemeChange('dark')}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      localSettings.appearance.theme === 'dark'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                    }`}
                  >
                    <Moon className="h-6 w-6 mx-auto mb-2 text-indigo-500" />
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Oscuro</p>
                  </button>

                  <button
                    onClick={() => handleThemeChange('system')}
                    className={`p-4 rounded-xl border-2 transition-all ${
                      localSettings.appearance.theme === 'system'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'
                    }`}
                  >
                    <Monitor className="h-6 w-6 mx-auto mb-2 text-gray-500" />
                    <p className="text-sm font-medium text-gray-800 dark:text-gray-200">Sistema</p>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
};

export default SettingsPage;
