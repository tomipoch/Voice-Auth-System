import { clsx } from 'clsx';

const Button = ({ 
  children, 
  className = '', 
  variant = 'primary', 
  size = 'md', 
  disabled = false,
  loading = false,
  ...props 
}) => {
  const baseClasses = 'font-medium rounded-lg focus:ring-4 focus:outline-none transition-colors';
  
  const variantClasses = {
    primary: 'text-white bg-blue-700 hover:bg-blue-800 focus:ring-blue-300',
    secondary: 'text-gray-900 bg-white border border-gray-300 hover:bg-gray-100 focus:ring-gray-200',
    success: 'text-white bg-green-700 hover:bg-green-800 focus:ring-green-300',
    danger: 'text-white bg-red-700 hover:bg-red-800 focus:ring-red-300',
    warning: 'text-white bg-yellow-500 hover:bg-yellow-600 focus:ring-yellow-300',
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const disabledClasses = disabled || loading 
    ? 'opacity-50 cursor-not-allowed' 
    : '';

  const classes = clsx(
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    disabledClasses,
    className
  );

  return (
    <button 
      className={classes} 
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <div className="flex items-center">
          <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Cargando...
        </div>
      ) : children}
    </button>
  );
};

export default Button;