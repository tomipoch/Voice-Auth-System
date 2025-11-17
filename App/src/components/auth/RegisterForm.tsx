import { useState, FormEvent, ChangeEvent } from 'react';
import { Eye, EyeOff, User, Mail, Lock, AlertCircle, CheckCircle } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Card from '../ui/Card';

interface RegisterFormData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
}

interface ValidationErrors {
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
}

interface RegisterFormProps {
  onSubmit: (data: Omit<RegisterFormData, 'confirmPassword'>) => void;
  isLoading?: boolean;
  error?: string | null;
}

const RegisterForm = ({ onSubmit, isLoading = false, error = null }: RegisterFormProps) => {
  const [formData, setFormData] = useState<RegisterFormData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});

  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};

    if (!formData.name) {
      errors.name = 'El nombre es requerido';
    } else if (formData.name.length < 2) {
      errors.name = 'El nombre debe tener al menos 2 caracteres';
    }

    if (!formData.email) {
      errors.email = 'El correo electrónico es requerido';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'El correo electrónico no es válido';
    }

    if (!formData.password) {
      errors.password = 'La contraseña es requerida';
    } else if (formData.password.length < 8) {
      errors.password = 'La contraseña debe tener al menos 8 caracteres';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      errors.password =
        'La contraseña debe contener al menos una mayúscula, una minúscula y un número';
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Confirma tu contraseña';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Las contraseñas no coinciden';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (validateForm()) {
      const { confirmPassword: _, ...submitData } = formData;
      onSubmit(submitData);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Limpiar error de validación cuando el usuario empieza a escribir
    if (validationErrors[name as keyof ValidationErrors]) {
      setValidationErrors((prev) => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const getPasswordStrength = (): {
    strength: string;
    color: string;
    width: string;
  } | null => {
    const password = formData.password;
    if (!password) return null;

    let score = 0;
    if (password.length >= 8) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;

    if (score < 3) return { strength: 'Débil', color: 'bg-red-500', width: 'w-1/3' };
    if (score < 4) return { strength: 'Media', color: 'bg-yellow-500', width: 'w-2/3' };
    return { strength: 'Fuerte', color: 'bg-green-500', width: 'w-full' };
  };

  const passwordStrength = getPasswordStrength();

  return (
    <Card className="w-full max-w-md p-8">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full mx-auto flex items-center justify-center mb-4">
          <User className="h-8 w-8 text-blue-600 dark:text-blue-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Crear Cuenta</h2>
        <p className="text-gray-600 dark:text-gray-400 dark:text-gray-500 dark:text-gray-400">
          Regístrate para acceder al sistema de autenticación por voz
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="name"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Nombre Completo
          </label>
          <div className="relative">
            <Input
              id="name"
              name="name"
              type="text"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Tu nombre completo"
              className={`pl-10 ${validationErrors.name ? 'border-red-300' : ''}`}
              disabled={isLoading}
            />
            <User className="absolute left-3 top-3 h-4 w-4 text-gray-400 dark:text-gray-500 dark:text-gray-400" />
          </div>
          {validationErrors.name && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.name}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Correo Electrónico
          </label>
          <div className="relative">
            <Input
              id="email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              placeholder="correo@ejemplo.com"
              className={`pl-10 ${validationErrors.email ? 'border-red-300' : ''}`}
              disabled={isLoading}
            />
            <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400 dark:text-gray-500 dark:text-gray-400" />
          </div>
          {validationErrors.email && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.email}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Contraseña
          </label>
          <div className="relative">
            <Input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange}
              placeholder="••••••••"
              className={`pl-10 pr-10 ${validationErrors.password ? 'border-red-300' : ''}`}
              disabled={isLoading}
            />
            <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400 dark:text-gray-500 dark:text-gray-400" />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-3 text-gray-400 dark:text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:text-gray-400 dark:text-gray-500 dark:text-gray-400"
              disabled={isLoading}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>

          {/* Indicador de fortaleza de contraseña */}
          {formData.password && passwordStrength && (
            <div className="mt-2">
              <div className="flex items-center space-x-2">
                <div className="h-2 flex-1 rounded-full bg-gray-200 dark:bg-gray-700">
                  <div
                    className={`h-2 rounded-full ${passwordStrength.color} transition-all duration-300 ${passwordStrength.width}`}
                  />
                </div>
                <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                  {passwordStrength.strength}
                </span>
              </div>
            </div>
          )}

          {validationErrors.password && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.password}</p>
          )}
        </div>

        <div>
          <label
            htmlFor="confirmPassword"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Confirmar Contraseña
          </label>
          <div className="relative">
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type={showConfirmPassword ? 'text' : 'password'}
              value={formData.confirmPassword}
              onChange={handleInputChange}
              placeholder="••••••••"
              className={`pl-10 pr-10 ${validationErrors.confirmPassword ? 'border-red-300' : ''}`}
              disabled={isLoading}
            />
            <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400 dark:text-gray-500 dark:text-gray-400" />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-3 text-gray-400 dark:text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:text-gray-400 dark:text-gray-500 dark:text-gray-400"
              disabled={isLoading}
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>

            {/* Indicador de coincidencia */}
            {formData.confirmPassword && formData.password && (
              <div className="absolute right-10 top-3">
                {formData.password === formData.confirmPassword ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-red-500" />
                )}
              </div>
            )}
          </div>
          {validationErrors.confirmPassword && (
            <p className="mt-1 text-sm text-red-600">{validationErrors.confirmPassword}</p>
          )}
        </div>

        <Button type="submit" className="w-full" size="lg" loading={isLoading} disabled={isLoading}>
          {isLoading ? 'Creando cuenta...' : 'Crear Cuenta'}
        </Button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400 dark:text-gray-500 dark:text-gray-400">
          ¿Ya tienes una cuenta?{' '}
          <a
            href="/login"
            className="font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500"
          >
            Inicia sesión aquí
          </a>
        </p>
      </div>
    </Card>
  );
};

export default RegisterForm;
