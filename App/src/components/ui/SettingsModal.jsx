import { useState, useEffect } from 'react';
import { User, Shield, Bell, Palette, Save, Eye, EyeOff, Mic, Clock, Mail, Smartphone, AlertTriangle, Download, Globe, Type, ChevronDown } from 'lucide-react';
import Modal from './Modal';
import Card from './Card';
import Button from './Button';
import { useAuth } from '../../hooks/useAuth';
import { useTheme } from '../../hooks/useTheme';

const SettingsModal = ({ isOpen, onClose }) => {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('profile');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Estados del formulario
  const [profileData, setProfileData] = useState({
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
    email: user?.email || '',
    phone: user?.phone || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    pushNotifications: false,
    securityAlerts: true,
    systemUpdates: false
  });

  const [securitySettings, setSecuritySettings] = useState({
    twoFactorAuth: false,
    biometricVerification: true,
    sessionTimeout: 30,
    loginNotifications: true
  });

  const [appearance, setAppearance] = useState({
    theme: 'light',
    language: 'es',
    fontSize: 'medium'
  });

  // Inicializar tema desde el contexto
  useEffect(() => {
    setAppearance(prev => ({
      ...prev,
      theme: theme
    }));
  }, [theme]);

  const handleSave = async (section) => {
    setIsLoading(true);
    try {
      // Si es la sección de apariencia, aplicar el tema
      if (section === 'appearance') {
        setTheme(appearance.theme);
      }
      
      // Simular guardado
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log(`Guardando configuración de ${section}`);
    } catch (error) {
      console.error('Error al guardar:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Perfil', icon: User },
    { id: 'security', label: 'Seguridad', icon: Shield },
    { id: 'notifications', label: 'Notificaciones', icon: Bell },
    { id: 'appearance', label: 'Apariencia', icon: Palette }
  ];

  // Estilos para inputs mejorados
  const inputClassName = `
    w-full px-6 py-4 rounded-2xl transition-all duration-300
    bg-gradient-to-r from-white/90 to-white/70 dark:from-gray-700/90 dark:to-gray-800/70 backdrop-blur-md border border-gray-200 dark:border-gray-700/50 dark:border-gray-600/50
    focus:ring-4 focus:ring-blue-300/30 dark:focus:ring-blue-500/30 focus:border-blue-400 dark:focus:border-blue-500 focus:bg-gradient-to-r focus:from-white/95 focus:to-white/80 dark:focus:from-gray-700/95 dark:focus:to-gray-800/80
    hover:bg-gradient-to-r hover:from-white/95 hover:to-white/80 dark:hover:from-gray-700/95 dark:hover:to-gray-800/80 hover:border-gray-300/60 dark:hover:border-gray-600/60 hover:shadow-xl
    placeholder:text-gray-500 dark:text-gray-400 dark:placeholder:text-gray-400 text-gray-800 dark:text-gray-100 font-medium text-lg
    shadow-xl
  `;

  const selectClassName = inputClassName;

  const renderProfileTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto pr-2">
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-3">
            <User className="h-4 w-4 text-white" />
          </div>
          Información Personal
        </h3>
        <div className="p-6 rounded-2xl hover:shadow-lg"
             style={{
               background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
               border: '1px solid rgba(0, 0, 0, 0.1)'
             }}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">Nombre</label>
              <input
                type="text"
                value={profileData.firstName}
                onChange={(e) => setProfileData({...profileData, firstName: e.target.value})}
                className={inputClassName}
                placeholder="Tu nombre"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">Apellido</label>
              <input
                type="text"
                value={profileData.lastName}
                onChange={(e) => setProfileData({...profileData, lastName: e.target.value})}
                className={inputClassName}
                placeholder="Tu apellido"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Email</label>
              <input
                type="email"
                value={profileData.email}
                onChange={(e) => setProfileData({...profileData, email: e.target.value})}
                className={inputClassName}
                placeholder="tu@email.com"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Teléfono</label>
              <input
                type="tel"
                value={profileData.phone}
                onChange={(e) => setProfileData({...profileData, phone: e.target.value})}
                className={inputClassName}
                placeholder="+1 234 567 890"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mr-3">
            <Shield className="h-4 w-4 text-white" />
          </div>
          Cambiar Contraseña
        </h3>
        <div className="space-y-6">
          <div className="p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <label className="block text-sm font-semibold text-gray-700 mb-3">Contraseña Actual</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={profileData.currentPassword}
                onChange={(e) => setProfileData({...profileData, currentPassword: e.target.value})}
                className={`${inputClassName} pr-12`}
                placeholder="Tu contraseña actual"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-4 flex items-center hover:bg-gray-100/50 rounded-r-xl"
              >
                {showPassword ? <EyeOff className="h-5 w-5 text-gray-400" /> : <Eye className="h-5 w-5 text-gray-400" />}
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl hover:shadow-lg"
                 style={{
                   background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                   border: '1px solid rgba(0, 0, 0, 0.1)'
                 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Nueva Contraseña</label>
              <input
                type={showPassword ? "text" : "password"}
                value={profileData.newPassword}
                onChange={(e) => setProfileData({...profileData, newPassword: e.target.value})}
                className={inputClassName}
                placeholder="Nueva contraseña"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
            </div>
            <div className="p-6 rounded-2xl hover:shadow-lg"
                 style={{
                   background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                   border: '1px solid rgba(0, 0, 0, 0.1)'
                 }}>
              <label className="block text-sm font-semibold text-gray-700 mb-3">Confirmar Contraseña</label>
              <input
                type={showPassword ? "text" : "password"}
                value={profileData.confirmPassword}
                onChange={(e) => setProfileData({...profileData, confirmPassword: e.target.value})}
                className={inputClassName}
                placeholder="Confirma tu contraseña"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(59, 130, 246, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <Button 
        onClick={() => handleSave('profile')} 
        disabled={isLoading} 
        className="w-full md:w-auto bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl px-8 py-3"
      >
        <Save className="h-4 w-4 mr-2" />
        {isLoading ? 'Guardando...' : 'Guardar Cambios'}
      </Button>
    </div>
  );

  const renderSecurityTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto pr-2">
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-pink-600 flex items-center justify-center mr-3">
            <Shield className="h-4 w-4 text-white" />
          </div>
          Configuración de Seguridad
        </h3>
        <div className="space-y-6">
          {/* Toggle mejorado para 2FA */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg" 
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-4">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Autenticación de Dos Factores</h4>
                <p className="text-sm text-gray-600">Añade una capa extra de seguridad a tu cuenta</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={securitySettings.twoFactorAuth}
                onChange={(e) => setSecuritySettings({...securitySettings, twoFactorAuth: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-indigo-600 shadow-lg"></div>
            </label>
          </div>

          {/* Toggle mejorado para Verificación Biométrica */}
          <div className="flex items-center justify-between p-6 rounded-2xl transition-all duration-300 hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center mr-4">
                <Mic className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Verificación Biométrica</h4>
                <p className="text-sm text-gray-600">Usar autenticación por voz como método principal</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={securitySettings.biometricVerification}
                onChange={(e) => setSecuritySettings({...securitySettings, biometricVerification: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-green-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-green-500 peer-checked:to-emerald-600 shadow-lg"></div>
            </label>
          </div>

          {/* Selector de tiempo de sesión mejorado */}
          <div className="p-6 rounded-2xl transition-all duration-300 hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center mr-4">
                <Clock className="h-5 w-5 text-white" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700">Tiempo de Sesión</label>
                <p className="text-xs text-gray-600">Duración antes del cierre automático</p>
              </div>
            </div>
            <select
              value={securitySettings.sessionTimeout}
              onChange={(e) => setSecuritySettings({...securitySettings, sessionTimeout: parseInt(e.target.value)})}
              className={selectClassName}
            >
              <option value={15}>15 minutos</option>
              <option value={30}>30 minutos</option>
              <option value={60}>1 hora</option>
              <option value={120}>2 horas</option>
            </select>
          </div>

          {/* Toggle para notificaciones de login */}
          <div className="flex items-center justify-between p-6 rounded-2xl transition-all duration-300 hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center mr-4">
                <Bell className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Notificaciones de Inicio de Sesión</h4>
                <p className="text-sm text-gray-600">Recibir alertas cuando alguien acceda a tu cuenta</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={securitySettings.loginNotifications}
                onChange={(e) => setSecuritySettings({...securitySettings, loginNotifications: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-amber-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-amber-500 peer-checked:to-orange-600 shadow-lg"></div>
            </label>
          </div>
        </div>
      </div>

      <Button 
        onClick={() => handleSave('security')} 
        disabled={isLoading} 
        className="w-full md:w-auto bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-lg hover:shadow-xl px-8 py-3"
      >
        <Save className="h-4 w-4 mr-2" />
        {isLoading ? 'Guardando...' : 'Guardar Configuración'}
      </Button>
    </div>
  );

  const renderNotificationsTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto overflow-x-hidden">
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mr-3">
            <Bell className="h-4 w-4 text-white" />
          </div>
          Preferencias de Notificación
        </h3>
        <div className="space-y-6">
          {/* Email Notifications */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-blue-600 flex items-center justify-center mr-4">
                <Mail className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Notificaciones por Email</h4>
                <p className="text-sm text-gray-600">Recibir notificaciones importantes por correo</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.emailNotifications}
                onChange={(e) => setNotificationSettings({...notificationSettings, emailNotifications: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-emerald-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-emerald-500 peer-checked:to-blue-600 shadow-lg"></div>
            </label>
          </div>

          {/* Push Notifications */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mr-4">
                <Smartphone className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Notificaciones Push</h4>
                <p className="text-sm text-gray-600">Notificaciones en tiempo real en el navegador</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.pushNotifications}
                onChange={(e) => setNotificationSettings({...notificationSettings, pushNotifications: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-indigo-600 shadow-lg"></div>
            </label>
          </div>

          {/* Security Alerts */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-orange-600 flex items-center justify-center mr-4">
                <AlertTriangle className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Alertas de Seguridad</h4>
                <p className="text-sm text-gray-600">Notificaciones sobre actividad sospechosa</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.securityAlerts}
                onChange={(e) => setNotificationSettings({...notificationSettings, securityAlerts: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-red-500 peer-checked:to-orange-600 shadow-lg"></div>
            </label>
          </div>

          {/* System Updates */}
          <div className="flex items-center justify-between p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mr-4">
                <Download className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Actualizaciones del Sistema</h4>
                <p className="text-sm text-gray-600">Información sobre nuevas funciones y actualizaciones</p>
              </div>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={notificationSettings.systemUpdates}
                onChange={(e) => setNotificationSettings({...notificationSettings, systemUpdates: e.target.checked})}
                className="sr-only peer"
              />
              <div className="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300/50 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white dark:bg-gray-900 after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-purple-500 peer-checked:to-pink-600 shadow-lg"></div>
            </label>
          </div>
        </div>
      </div>

      <Button 
        onClick={() => handleSave('notifications')} 
        disabled={isLoading}
        className="w-full md:w-auto bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl px-8 py-3"
      >
        <Save className="h-4 w-4 mr-2" />
        {isLoading ? 'Guardando...' : 'Guardar Preferencias'}
      </Button>
    </div>
  );

  const renderAppearanceTab = () => (
    <div className="space-y-8 max-h-96 overflow-y-auto overflow-x-hidden">
      <div>
        <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center mr-3">
            <Palette className="h-4 w-4 text-white" />
          </div>
          Personalización
        </h3>
        <div className="space-y-6">
          {/* Theme Setting */}
          <div className="p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Palette className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">Tema de la Aplicación</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">Elige el esquema de colores preferido</p>
              </div>
            </div>
            <div className="relative">
              <select
                value={appearance.theme}
                onChange={(e) => {
                  const newTheme = e.target.value;
                  setAppearance({...appearance, theme: newTheme});
                  // Aplicar el tema inmediatamente
                  setTheme(newTheme);
                }}
                className="w-full px-6 py-4 bg-gradient-to-r from-white/90 to-white/70 dark:from-gray-800/90 dark:to-gray-700/70 backdrop-blur-md border border-indigo-200/50 dark:border-gray-600/50 rounded-2xl focus:ring-4 focus:ring-indigo-300/30 dark:focus:ring-indigo-500/30 focus:border-indigo-400 dark:focus:border-indigo-500 shadow-xl text-gray-800 dark:text-gray-100 font-semibold text-lg appearance-none cursor-pointer hover:bg-gradient-to-r hover:from-white/95 hover:to-white/80 dark:hover:from-gray-800/95 dark:hover:to-gray-700/80 hover:shadow-2xl pr-14"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              >
                <option value="light">🌞 Claro</option>
                <option value="dark">🌙 Oscuro</option>
                <option value="auto">🔄 Automático (Sistema)</option>
              </select>
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-6 w-6 text-indigo-500" />
              </div>
            </div>
          </div>

          {/* Language Setting */}
          <div className="p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <Globe className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Idioma de la Interfaz</h4>
                <p className="text-sm text-gray-600">Selecciona tu idioma preferido</p>
              </div>
            </div>
            <div className="relative">
              <select
                value={appearance.language}
                onChange={(e) => setAppearance({...appearance, language: e.target.value})}
                className="w-full px-6 py-4 bg-gradient-to-r from-white/90 to-white/70 backdrop-blur-md border border-emerald-200/50 rounded-2xl focus:ring-4 focus:ring-emerald-300/30 focus:border-emerald-400 shadow-xl text-gray-800 font-semibold text-lg appearance-none cursor-pointer hover:bg-gradient-to-r hover:from-white/95 hover:to-white/80 hover:shadow-2xl pr-14"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(16, 185, 129, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              >
                <option value="es">🇪🇸 Español</option>
                <option value="en">🇺🇸 English</option>
                <option value="pt">🇧🇷 Português</option>
              </select>
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-6 w-6 text-emerald-500" />
              </div>
            </div>
          </div>

          {/* Font Size Setting */}
          <div className="p-6 rounded-2xl hover:shadow-lg"
               style={{
                 background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(248, 250, 252, 0.8) 100%)',
                 border: '1px solid rgba(0, 0, 0, 0.1)'
               }}>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
                <Type className="h-5 w-5 text-white" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-800">Tamaño de Fuente</h4>
                <p className="text-sm text-gray-600">Ajusta el tamaño del texto para mejor legibilidad</p>
              </div>
            </div>
            <div className="relative">
              <select
                value={appearance.fontSize}
                onChange={(e) => setAppearance({...appearance, fontSize: e.target.value})}
                className="w-full px-6 py-4 bg-gradient-to-r from-white/90 to-white/70 backdrop-blur-md border border-orange-200/50 rounded-2xl focus:ring-4 focus:ring-orange-300/30 focus:border-orange-400 shadow-xl text-gray-800 font-semibold text-lg appearance-none cursor-pointer hover:bg-gradient-to-r hover:from-white/95 hover:to-white/80 hover:shadow-2xl pr-14"
                style={{
                  background: 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.7) 100%)',
                  backdropFilter: 'blur(20px)',
                  boxShadow: '0 8px 32px rgba(251, 146, 60, 0.15), inset 0 1px 0 rgba(255,255,255,0.6)'
                }}
              >
                <option value="small">📏 Pequeño</option>
                <option value="medium">📐 Mediano</option>
                <option value="large">📊 Grande</option>
              </select>
              <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none">
                <ChevronDown className="h-6 w-6 text-orange-500" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <Button 
        onClick={() => handleSave('appearance')} 
        disabled={isLoading}
        className="w-full md:w-auto bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 text-white shadow-lg hover:shadow-xl px-8 py-3"
      >
        <Save className="h-4 w-4 mr-2" />
        {isLoading ? 'Guardando...' : 'Guardar Apariencia'}
      </Button>
    </div>
  );

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
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title="⚙️ Configuración"
      size="xl"
    >
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar de configuración mejorado */}
        <div className="lg:col-span-1">
          <div 
            className="relative overflow-hidden rounded-2xl p-4 shadow-lg border"
            style={{
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(59, 130, 246, 0.2)'
            }}
          >
            {/* Elemento decorativo */}
            <div 
              className="absolute top-0 right-0 w-20 h-20 rounded-full opacity-30"
              style={{
                background: 'linear-gradient(135deg, #3B82F6, #8B5CF6)',
                filter: 'blur(20px)'
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
                      ${activeTab === tab.id
                        ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-[1.02]' 
                        : 'text-gray-700 dark:text-gray-300 hover:bg-white dark:bg-gray-900/60 dark:hover:bg-gray-700/60 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-md hover:scale-[1.01]'
                      }
                    `}
                  >
                    {/* Efecto de brillo en hover */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 transform translate-x-[-100%] group-hover:translate-x-[100%] transition-all duration-700" />
                    
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
          <div 
            className="relative overflow-hidden rounded-2xl p-8 shadow-lg border min-h-96"
            style={{
              background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0.7) 100%)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.3)'
            }}
          >
            {/* Elementos decorativos de fondo */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div 
                className="absolute -top-20 -right-20 w-40 h-40 rounded-full opacity-10"
                style={{
                  background: 'linear-gradient(135deg, #06B6D4, #3B82F6)',
                  filter: 'blur(30px)'
                }}
              />
              <div 
                className="absolute -bottom-20 -left-20 w-40 h-40 rounded-full opacity-10"
                style={{
                  background: 'linear-gradient(135deg, #8B5CF6, #3B82F6)',
                  filter: 'blur(30px)'
                }}
              />
            </div>
            
            <div className="relative z-10">
              {renderTabContent()}
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default SettingsModal;