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
  const baseClasses = 'relative font-semibold rounded-xl focus:ring-4 focus:outline-none transition-all duration-300 hover:scale-[1.02] backdrop-blur-sm';
  
  const variantClasses = {
    primary: 'text-white bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 focus:ring-blue-500/50 shadow-lg hover:shadow-xl',
    secondary: 'text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-900/80 dark:bg-gray-800/80 border border-blue-200/50 dark:border-gray-600/50 hover:bg-white dark:bg-gray-900/90 dark:hover:bg-gray-800/90 hover:border-blue-300/60 dark:hover:border-gray-500/60 focus:ring-blue-300/50 dark:focus:ring-gray-500/50 shadow-sm hover:shadow-md backdrop-blur-xl',
    success: 'text-white bg-gradient-to-r from-emerald-500 to-green-600 hover:from-emerald-400 hover:to-green-500 focus:ring-emerald-500/50 shadow-lg hover:shadow-xl',
    danger: 'text-white bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 focus:ring-red-500/50 shadow-lg hover:shadow-xl',
    warning: 'text-white bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 focus:ring-amber-500/50 shadow-lg hover:shadow-xl',
    glass: 'text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-900/60 dark:bg-gray-800/60 border border-blue-200/40 dark:border-gray-600/40 hover:bg-white dark:bg-gray-900/70 dark:hover:bg-gray-800/70 hover:border-blue-300/50 dark:hover:border-gray-500/50 focus:ring-blue-300/50 dark:focus:ring-gray-500/50 shadow-xl hover:shadow-2xl backdrop-blur-xl',
  };

  const sizeClasses = {
    sm: 'px-4 py-2.5 text-sm',
    md: 'px-6 py-3 text-sm',
    lg: 'px-8 py-4 text-base',
  };

  const disabledClasses = disabled || loading 
    ? 'opacity-50 cursor-not-allowed transform-none hover:scale-100' 
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
        <div className="flex items-center justify-center">
          <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin mr-2"></div>
          Cargando...
        </div>
      ) : children}
    </button>
  );
};

export default Button;