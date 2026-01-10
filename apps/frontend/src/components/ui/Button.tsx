import { clsx } from 'clsx';
import { memo, type ButtonHTMLAttributes, type ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  className?: string;
  variant?:
    | 'primary'
    | 'secondary'
    | 'success'
    | 'danger'
    | 'warning'
    | 'glass'
    | 'ghost'
    | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
}

const Button = memo(
  ({
    children,
    className = '',
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    ...props
  }: ButtonProps) => {
    const baseClasses =
      'relative font-semibold rounded-xl focus:ring-4 focus:outline-none transition-all duration-300 hover:scale-[1.02] backdrop-blur-sm';

    const variantClasses = {
      primary:
        'text-white bg-linear-to-r from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 focus:ring-blue-500/50 shadow-lg hover:shadow-xl',
      secondary:
        'text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-900/80 dark:bg-gray-800/80 border border-blue-200/50 dark:border-gray-600/50 hover:bg-white dark:bg-gray-900/90 dark:hover:bg-gray-800/90 hover:border-blue-300/60 dark:hover:border-gray-500/60 focus:ring-blue-300/50 dark:focus:ring-gray-500/50 shadow-sm hover:shadow-md backdrop-blur-xl',
      success:
        'text-white bg-linear-to-r from-emerald-500 to-green-600 hover:from-emerald-400 hover:to-green-500 focus:ring-emerald-500/50 shadow-lg hover:shadow-xl',
      danger:
        'text-white bg-linear-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 focus:ring-red-500/50 shadow-lg hover:shadow-xl',
      warning:
        'text-white bg-linear-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 focus:ring-amber-500/50 shadow-lg hover:shadow-xl',
      glass:
        'bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 shadow-lg hover:shadow-xl',
      ghost:
        'bg-transparent hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300',
      outline:
        'bg-transparent border-2 border-blue-500 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20',
    };

    const sizeClasses = {
      sm: 'px-4 h-9 text-sm',
      md: 'px-6 h-11 text-sm',
      lg: 'px-8 h-14 text-base',
    };

    const disabledClasses =
      disabled || loading ? 'opacity-50 cursor-not-allowed transform-none hover:scale-100' : '';

    const classes = clsx(
      baseClasses,
      variantClasses[variant],
      sizeClasses[size],
      disabledClasses,
      className
    );

    return (
      <button className={classes} disabled={disabled || loading} {...props}>
        {loading ? (
          <div className="flex items-center justify-center">
            <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin mr-2"></div>
            Cargando...
          </div>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
