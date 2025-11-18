import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mic } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

interface FormData {
  email: string;
  password: string;
}

interface FormErrors {
  email?: string;
  password?: string;
}

const LoginPage = () => {
  const [formData, setFormData] = useState<FormData>({
    email: '',
    password: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});

  const { login, isLoading } = useAuth();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!formData.email) {
      newErrors.email = 'El email es requerido';
    } else if (!emailRegex.test(formData.email)) {
      newErrors.email = 'Email inválido';
    }

    if (!formData.password) {
      newErrors.password = 'La contraseña es requerida';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    await login({ email: formData.email, password: formData.password });
  };

  // Función para usar credenciales de desarrollo
  const fillDevCredentials = (email: string, password: string) => {
    setFormData({ email, password });
    setErrors({});
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 dark:bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/20 dark:bg-blue-600/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/20 dark:bg-cyan-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          {/* Header */}
          <div className="text-center">
            {/* Liquid Glass Icon Container */}
            <div className="mx-auto relative">
              <div className="h-20 w-20 mx-auto bg-gradient-to-br from-white/70 to-white/40 backdrop-blur-xl rounded-3xl border border-blue-200/30 shadow-xl flex items-center justify-center group hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-blue-600/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <Mic className="h-10 w-10 text-blue-600 dark:text-blue-400 relative z-10" />
              </div>
            </div>

            <h2 className="mt-8 text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-blue-800 bg-clip-text text-transparent">
              Iniciar Sesión
            </h2>
            <p className="mt-3 text-lg text-blue-600 dark:text-blue-400/80 font-medium">
              Sistema de Autenticación Biométrica
            </p>
          </div>

          {/* Development Panel with Liquid Glass Effect */}
          {import.meta.env.DEV && (
            <div className="backdrop-blur-xl bg-white dark:bg-gray-900/60 border border-blue-200/40 rounded-2xl p-6 shadow-xl">
              <div className="text-center mb-4">
                <h3 className="text-sm font-semibold text-blue-700 mb-2 flex items-center justify-center gap-2">
                  <span className="text-lg">🚀</span>
                  Usuarios de Prueba Disponibles
                </h3>
              </div>

              <div className="space-y-3">
                {/* Usuarios de prueba */}
                <div className="text-xs text-gray-600 dark:text-gray-400 font-semibold mb-2">
                  👥 USUARIOS DE PRUEBA:
                </div>
                <button
                  type="button"
                  onClick={() => fillDevCredentials('juan.perez@empresa.com', 'UserVoice2024!')}
                  className="w-full text-left text-sm bg-green-100/80 backdrop-blur-sm hover:bg-green-200/80 text-green-700 py-3 px-4 rounded-xl border border-green-300/40 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg"
                >
                  <div>
                    <span className="mr-2">👤</span>
                    <strong>Juan Carlos Pérez</strong>
                    <div className="text-xs text-green-600/70 mt-1">juan.perez@empresa.com</div>
                    <div className="text-xs text-green-600 mt-1">🎤 Perfil de voz configurado</div>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() =>
                    fillDevCredentials('maria.rodriguez@empresa.com', 'UserVoice2024!')
                  }
                  className="w-full text-left text-sm bg-yellow-100/80 backdrop-blur-sm hover:bg-yellow-200/80 text-yellow-700 py-3 px-4 rounded-xl border border-yellow-300/40 transition-all duration-300 hover:scale-[1.02] hover:shadow-lg"
                >
                  <div>
                    <span className="mr-2">👤</span>
                    <strong>María Elena Rodríguez</strong>
                    <div className="text-xs text-yellow-600/70 mt-1">
                      maria.rodriguez@empresa.com
                    </div>
                    <div className="text-xs text-orange-600 mt-1">⚠️ Sin perfil de voz</div>
                  </div>
                </button>
                {/* Usuarios de desarrollo */}
                <div className="text-xs text-gray-600 dark:text-gray-400 font-semibold mt-4 mb-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                  🔧 DESARROLLO:
                </div>
                <button
                  type="button"
                  onClick={() => fillDevCredentials('juan.perez@empresaa.com', 'User2024!')}
                  className="w-full text-xs bg-green-100/80 backdrop-blur-sm hover:bg-green-200/80 text-green-700 py-2 px-3 rounded-xl border border-green-300/40 transition-all duration-300 hover:scale-[1.02]"
                >
                  <span className="mr-1">👤</span>
                  <strong>Juan Carlos Pérez</strong>
                  <div className="text-xs text-green-600/70 mt-1">juan.perez@empresaa.com</div>
                </button>
                <button
                  type="button"
                  onClick={() => fillDevCredentials('carlos.rodriguez@empresab.com', 'User2024!')}
                  className="w-full text-xs bg-green-100/80 backdrop-blur-sm hover:bg-green-200/80 text-green-700 py-2 px-3 rounded-xl border border-green-300/40 transition-all duration-300 hover:scale-[1.02]"
                >
                  <span className="mr-1">👤</span>
                  <strong>Carlos Rodríguez Silva</strong>
                  <div className="text-xs text-green-600/70 mt-1">
                    carlos.rodriguez@empresab.com
                  </div>
                </button>
                {/* Usuarios de desarrollo */}
                <div className="text-xs text-gray-600 dark:text-gray-400 font-semibold mt-4 mb-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                  🔧 DESARROLLO:
                </div>
                <button
                  type="button"
                  onClick={() => fillDevCredentials('dev@test.com', '123456')}
                  className="w-full text-xs bg-blue-100/80 backdrop-blur-sm hover:bg-blue-200/80 text-blue-700 py-2 px-3 rounded-xl border border-blue-300/40 transition-all duration-300 hover:scale-[1.02]"
                >
                  <span className="mr-1">👤</span>
                  <strong>Usuario de Desarrollo</strong>
                  <div className="text-xs text-blue-600 dark:text-blue-400/70 mt-1">
                    dev@test.com
                  </div>
                </button>{' '}
                <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="text-xs text-gray-500 dark:text-gray-400 text-center p-2 bg-amber-50/80 rounded-lg border border-amber-200/60 mb-3">
                    <span className="text-amber-600">💡</span> <strong>¿Eres administrador?</strong>
                    <br />
                    Las credenciales administrativas están en el{' '}
                    <Link
                      to="/admin/login"
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-700 underline"
                    >
                      login administrativo
                    </Link>
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                    💡 Haz clic en cualquier usuario para autocompletar el formulario
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Main Form with Liquid Glass Effect */}
          <div className="backdrop-blur-xl bg-white dark:bg-gray-900/70 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* Email Input */}
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Correo Electrónico
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="tu@ejemplo.com"
                />
                {errors.email && <p className="text-sm text-red-500">{errors.email}</p>}
              </div>

              {/* Password Input */}
              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Contraseña
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="••••••••"
                />
                {errors.password && <p className="text-sm text-red-500">{errors.password}</p>}
              </div>

              {/* Register Link */}
              <div className="text-center pt-2 space-y-2">
                <Link
                  to="/register"
                  className="block text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 transition-colors duration-300"
                >
                  ¿No tienes cuenta? Regístrate aquí
                </Link>
                <Link
                  to="/admin/login"
                  className="block text-xs font-medium text-red-600 hover:text-red-700 transition-colors duration-300 border-t border-blue-200/30 pt-2"
                >
                  🛡️ Acceso Administrativo
                </Link>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full relative py-3 px-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <span className="relative z-10">
                  {isLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      Iniciando sesión...
                    </div>
                  ) : (
                    'Iniciar Sesión'
                  )}
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-blue-500 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
              </button>
            </form>
          </div>

          {/* Footer Info */}
          <div className="text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400/70 leading-relaxed">
              🔐 Sistema de autenticación biométrica por voz
              <br />
              <span className="text-xs text-blue-500/50">
                Tecnología de vanguardia para tu seguridad
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
