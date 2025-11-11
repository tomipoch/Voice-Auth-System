import { useState } from 'react';
import { Link } from 'react-router-dom';
import { UserPlus, Mail, Lock, User } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card from '../components/ui/Card';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  
  const { register, isLoading } = useAuth();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Limpiar error del campo cuando el usuario empieza a escribir
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'El nombre es requerido';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'El nombre debe tener al menos 2 caracteres';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'El email es requerido';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'El formato del email no es válido';
    }

    if (!formData.password.trim()) {
      newErrors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }

    if (!formData.confirmPassword.trim()) {
      newErrors.confirmPassword = 'Confirma tu contraseña';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Las contraseñas no coinciden';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const result = await register({
      name: formData.name.trim(),
      email: formData.email.trim().toLowerCase(),
      password: formData.password,
    });

    if (result.success) {
      // Resetear formulario después del registro exitoso
      setFormData({
        name: '',
        email: '',
        password: '',
        confirmPassword: '',
      });
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/20 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          
          {/* Header */}
          <div className="text-center">
            {/* Liquid Glass Icon Container */}
            <div className="mx-auto relative">
              <div className="h-20 w-20 mx-auto bg-gradient-to-br from-white/70 to-white/40 backdrop-blur-xl rounded-3xl border border-blue-200/30 shadow-xl flex items-center justify-center group hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-400/20 to-blue-600/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <UserPlus className="h-10 w-10 text-blue-600 dark:text-blue-400 relative z-10" />
              </div>
            </div>
            
            <h2 className="mt-8 text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-indigo-800 bg-clip-text text-transparent">
              Crear Cuenta
            </h2>
            <p className="mt-3 text-lg text-blue-600 dark:text-blue-400/80 font-medium">
              Únete al sistema de autenticación biométrica
            </p>
          </div>

          {/* Main Form with Liquid Glass Effect */}
          <div className="backdrop-blur-xl bg-white dark:bg-gray-900/70 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* Name Input */}
              <div className="relative space-y-2">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Nombre Completo
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  autoComplete="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="Tu nombre completo"
                />
                <User className="absolute right-3 top-9 h-5 w-5 text-blue-400" />
                {errors.name && (
                  <p className="text-sm text-red-500">{errors.name}</p>
                )}
              </div>

              {/* Email Input */}
              <div className="relative space-y-2">
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
                  className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="tu@ejemplo.com"
                />
                <Mail className="absolute right-3 top-9 h-5 w-5 text-blue-400" />
                {errors.email && (
                  <p className="text-sm text-red-500">{errors.email}</p>
                )}
              </div>

              {/* Password Input */}
              <div className="relative space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Contraseña
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="••••••••"
                />
                <Lock className="absolute right-3 top-9 h-5 w-5 text-blue-400" />
                {errors.password && (
                  <p className="text-sm text-red-500">{errors.password}</p>
                )}
              </div>

              {/* Confirm Password Input */}
              <div className="relative space-y-2">
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
                  Confirmar Contraseña
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="••••••••"
                />
                <Lock className="absolute right-3 top-9 h-5 w-5 text-blue-400" />
                {errors.confirmPassword && (
                  <p className="text-sm text-red-500">{errors.confirmPassword}</p>
                )}
              </div>

              {/* Login Link */}
              <div className="text-center pt-2">
                <Link 
                  to="/login" 
                  className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 transition-colors duration-300"
                >
                  ¿Ya tienes cuenta? Inicia sesión aquí
                </Link>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full relative py-3 px-6 bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                <span className="relative z-10">
                  {isLoading ? (
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                      Creando cuenta...
                    </div>
                  ) : (
                    'Crear Cuenta'
                  )}
                </span>
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400 to-indigo-500 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
              </button>
            </form>
          </div>

          {/* Footer Info */}
          <div className="text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400/70 leading-relaxed">
              🎤 Después del registro, configurarás tu perfil de voz
              <br />
              <span className="text-xs text-blue-500/50">Para completar la autenticación biométrica</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;