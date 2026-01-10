import { clsx } from 'clsx';
import type { InputHTMLAttributes, ReactNode } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  className?: string;
  id?: string;
  type?: string;
  icon?: ReactNode;
}

const Input = ({ label, error, className = '', id, type = 'text', icon, ...props }: InputProps) => {
  const inputClasses = clsx(
    'block w-full h-11 px-4 rounded-xl text-sm focus:ring-2 focus:outline-none transition-all duration-300 backdrop-blur-sm font-medium border',
    error
      ? 'border-red-300/60 dark:border-red-600/60 bg-red-50/80 dark:bg-red-900/20 text-red-900 dark:text-red-100 placeholder-red-400 dark:placeholder-red-400 focus:ring-red-500/50 focus:border-red-500/60 shadow-sm'
      : 'border-blue-200/50 dark:border-gray-600/50 bg-white dark:bg-gray-900/80 dark:bg-gray-800/80 text-gray-800 dark:text-gray-200 placeholder-gray-500 dark:placeholder-gray-400 focus:ring-blue-500/50 dark:focus:ring-blue-400/50 focus:border-blue-500/60 dark:focus:border-blue-400/60 shadow-sm hover:shadow-md border',
    className
  );

  const labelClasses = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2';
  const errorClasses = 'text-sm text-red-500 mt-1';

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={id} className={labelClasses}>
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-800 dark:text-gray-200 opacity-80">
            {icon}
          </div>
        )}
        <input id={id} type={type} className={clsx(inputClasses, icon && 'pl-10')} {...props} />
      </div>
      {error && <p className={errorClasses}>{error}</p>}
    </div>
  );
};

export default Input;
