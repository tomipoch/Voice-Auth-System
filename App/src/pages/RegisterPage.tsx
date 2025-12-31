import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus, Mail, Lock, User, CreditCard } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';

interface FormData {
  first_name: string;
  last_name: string;
  rut: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  first_name?: string;
  last_name?: string;
  rut?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

const RegisterPage = () => {
  const [formData, setFormData] = useState<FormData>({
    first_name: '',
    last_name: '',
    rut: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});

  const { register, isLoading } = useAuth();
  const navigate = useNavigate();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Limpiar error del campo cuando el usuario empieza a escribir
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({
        ...prev,
        [name]: undefined,
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.first_name.trim()) {
      newErrors.first_name = 'El nombre es requerido';
    } else if (formData.first_name.trim().length < 2) {
      newErrors.first_name = 'El nombre debe tener al menos 2 caracteres';
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = 'El apellido es requerido';
    } else if (formData.last_name.trim().length < 2) {
      newErrors.last_name = 'El apellido debe tener al menos 2 caracteres';
    }

    // Validar RUT
    if (!formData.rut.trim()) {
      newErrors.rut = 'El RUT es requerido';
    } else if (!validateRUT(formData.rut.trim())) {
      newErrors.rut = 'RUT inválido (formato: 12345678-9)';
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

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await register({
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        rut: formData.rut.trim(),
        email: formData.email.trim().toLowerCase(),
        password: formData.password,
      });

      // Mostrar mensaje de éxito
      toast.success('¡Cuenta creada exitosamente! Redirigiendo al login...');

      // Resetear formulario
      setFormData({
        first_name: '',
        last_name: '',
        rut: '',
        email: '',
        password: '',
        confirmPassword: '',
      });

      // Redirigir al login después de 1.5 segundos
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (error) {
      // El error ya es manejado por useAuth
      console.error('Error en registro:', error);
    }
  };

  // Función para validar RUT chileno
  const validateRUT = (rut: string): boolean => {
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
      sum += parseInt(rutNumber[i]!) * multiplier;
      multiplier = multiplier === 7 ? 2 : multiplier + 1;
    }

    const expectedVerifier = 11 - (sum % 11);
    const calculatedVerifier =
      expectedVerifier === 11 ? '0' : expectedVerifier === 10 ? 'K' : expectedVerifier.toString();

    return verifier === calculatedVerifier;
  };
  return (
    <div className="min-h-screen relative overflow-hidden bg-linear-to-br from-blue-50 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 dark:bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/20 dark:bg-indigo-600/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/20 dark:bg-cyan-500/10 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          {/* Header */}
          <div className="text-center">
            {/* Liquid Glass Icon Container */}
            <div className="mx-auto relative">
              <div className="h-20 w-20 mx-auto bg-linear-to-br from-white/70 to-white/40 backdrop-blur-xl rounded-3xl border border-blue-200/30 shadow-xl flex items-center justify-center group hover:scale-105 transition-all duration-300">
                <div className="absolute inset-0 bg-linear-to-br from-indigo-400/20 to-blue-600/20 rounded-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <UserPlus className="h-10 w-10 text-blue-600 dark:text-blue-400 relative z-10" />
              </div>
            </div>

            <h2 className="mt-8 text-4xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 bg-clip-text text-transparent">
              Crear Cuenta
            </h2>
            <p className="mt-3 text-lg text-blue-600 dark:text-blue-400/80 font-medium">
              Únete al sistema de autenticación biométrica
            </p>
          </div>

          {/* Main Form with Liquid Glass Effect */}
          <div className="backdrop-blur-xl bg-white dark:bg-gray-900/70 border border-blue-200/40 rounded-2xl p-8 shadow-xl">
            <form className="space-y-6" onSubmit={handleSubmit}>
              {/* First Name Input */}
              <div className="relative space-y-2">
                <label htmlFor="first_name" className="block text-sm font-medium text-gray-700">
                  Nombre
                </label>
                <input
                  id="first_name"
                  name="first_name"
                  type="text"
                  autoComplete="given-name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="Tu nombre"
                />
                <User className="absolute right-3 top-9 h-5 w-5 text-blue-400" />
                {errors.first_name && <p className="text-sm text-red-500">{errors.first_name}</p>}
              </div>

              {/* Last Name Input */}
              <div className="relative space-y-2">
                <label htmlFor="last_name" className="block text-sm font-medium text-gray-700">
                  Apellido
                </label>
                <input
                  id="last_name"
                  name="last_name"
                  type="text"
                  autoComplete="family-name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                  placeholder="Tu apellido"
                />
                <User className="absolute right-3 top-9 h-5 w-5 text-blue-400" />
                {errors.last_name && <p className="text-sm text-red-500">{errors.last_name}</p>}
              </div>

              {/* RUT Input - Split into number and verification digit */}
              <div className="relative space-y-2">
                <label htmlFor="rut_number" className="block text-sm font-medium text-gray-700">
                  RUT
                </label>
                <div className="flex gap-3 items-center">
                  {/* RUT Number */}
                  <div className="flex-1 relative">
                    <input
                      id="rut_number"
                      name="rut_number"
                      type="text"
                      autoComplete="off"
                      value={(() => {
                        // Extraer solo el número (antes del guión si existe)
                        if (!formData.rut) return '';
                        const parts = formData.rut.split('-');
                        return parts[0] || '';
                      })()}
                      onChange={(e) => {
                        const value = e.target.value.replace(/\D/g, '').slice(0, 8);
                        // Obtener el verificador actual si existe
                        const parts = formData.rut.split('-');
                        const verifier = parts.length > 1 ? parts[1] : '';

                        setFormData((prev) => ({
                          ...prev,
                          rut: value + (verifier ? `-${verifier}` : ''),
                        }));
                        if (errors.rut) {
                          setErrors((prev) => ({ ...prev, rut: undefined }));
                        }
                      }}
                      className="w-full px-4 py-3 pr-12 bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                      placeholder="12345678"
                      maxLength={8}
                    />
                    <CreditCard className="absolute right-3 top-3 h-5 w-5 text-blue-400" />
                  </div>

                  {/* Hyphen Separator */}
                  <div className="flex items-center text-gray-400 text-2xl font-bold pb-1">-</div>

                  {/* Verification Digit */}
                  <div className="w-20 relative">
                    <input
                      id="rut_verifier"
                      name="rut_verifier"
                      type="text"
                      autoComplete="off"
                      value={(() => {
                        // Extraer solo el verificador (después del guión si existe)
                        if (!formData.rut) return '';
                        const parts = formData.rut.split('-');
                        return parts.length > 1 ? parts[1] : '';
                      })()}
                      onChange={(e) => {
                        const value = e.target.value.toUpperCase().slice(0, 1);
                        if (value === '' || /^[0-9K]$/.test(value)) {
                          // Obtener el número actual
                          const parts = formData.rut.split('-');
                          const number = parts[0] || '';

                          setFormData((prev) => ({
                            ...prev,
                            rut: number + (value ? `-${value}` : ''),
                          }));
                          if (errors.rut) {
                            setErrors((prev) => ({ ...prev, rut: undefined }));
                          }
                        }
                      }}
                      className="w-full px-4 py-3 text-center bg-white dark:bg-gray-900/80 backdrop-blur-sm border border-blue-200/50 rounded-xl text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-300"
                      placeholder="9"
                      maxLength={1}
                    />
                  </div>
                </div>
                {errors.rut && <p className="text-sm text-red-500">{errors.rut}</p>}
                <p className="text-xs text-gray-500">Ingresa tu RUT sin puntos. Ej: 12345678-9</p>
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
                {errors.email && <p className="text-sm text-red-500">{errors.email}</p>}
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
                {errors.password && <p className="text-sm text-red-500">{errors.password}</p>}

                {/* Password Requirements */}
                <div className="mt-2 space-y-1">
                  <p className="text-xs font-medium text-gray-600">La contraseña debe tener:</p>
                  <ul className="text-xs space-y-1">
                    <li
                      className={`flex items-center gap-1 ${formData.password.length >= 8 ? 'text-green-600' : 'text-gray-500'}`}
                    >
                      <span className="text-lg">{formData.password.length >= 8 ? '✓' : '○'}</span>
                      Al menos 8 caracteres
                    </li>
                    <li
                      className={`flex items-center gap-1 ${/[A-Z]/.test(formData.password) ? 'text-green-600' : 'text-gray-500'}`}
                    >
                      <span className="text-lg">{/[A-Z]/.test(formData.password) ? '✓' : '○'}</span>
                      Una letra mayúscula
                    </li>
                    <li
                      className={`flex items-center gap-1 ${/[a-z]/.test(formData.password) ? 'text-green-600' : 'text-gray-500'}`}
                    >
                      <span className="text-lg">{/[a-z]/.test(formData.password) ? '✓' : '○'}</span>
                      Una letra minúscula
                    </li>
                    <li
                      className={`flex items-center gap-1 ${/\d/.test(formData.password) ? 'text-green-600' : 'text-gray-500'}`}
                    >
                      <span className="text-lg">{/\d/.test(formData.password) ? '✓' : '○'}</span>
                      Un número
                    </li>
                  </ul>
                </div>
              </div>

              {/* Confirm Password Input */}
              <div className="relative space-y-2">
                <label
                  htmlFor="confirmPassword"
                  className="block text-sm font-medium text-gray-700"
                >
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
                className="w-full relative py-3 px-6 bg-linear-to-r from-blue-500 to-indigo-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
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
                <div className="absolute inset-0 bg-linear-to-r from-blue-400 to-indigo-500 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
              </button>
            </form>
          </div>

          {/* Footer Info */}
          <div className="text-center">
            <p className="text-sm text-blue-600 dark:text-blue-400/70 leading-relaxed">
              🎤 Después del registro, configurarás tu perfil de voz
              <br />
              <span className="text-xs text-blue-500/50">
                Para completar la autenticación biométrica
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
