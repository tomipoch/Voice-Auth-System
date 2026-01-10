import { clsx } from 'clsx';
import type { SelectHTMLAttributes, ReactNode } from 'react';

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  className?: string;
  id?: string;
  children: ReactNode;
}

const Select = ({ label, error, className = '', id, children, ...props }: SelectProps) => {
  const selectClasses = clsx(
    'block w-full h-11 px-4 rounded-xl text-sm focus:ring-2 focus:outline-none transition-all duration-300 backdrop-blur-sm font-medium border appearance-none cursor-pointer',
    error
      ? 'border-red-300/60 dark:border-red-600/60 bg-red-50/80 dark:bg-red-900/20 text-red-900 dark:text-red-100 focus:ring-red-500/50 focus:border-red-500/60 shadow-sm'
      : 'border-blue-200/50 dark:border-gray-600/50 bg-white dark:bg-gray-900/80 dark:bg-gray-800/80 text-gray-800 dark:text-gray-200 focus:ring-blue-500/50 dark:focus:ring-blue-400/50 focus:border-blue-500/60 shadow-sm hover:shadow-md',
    className
  );

  const containerClasses = 'relative';
  const labelClasses = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2';
  const errorClasses = 'text-sm text-red-500 mt-1';

  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={id} className={labelClasses}>
          {label}
        </label>
      )}
      <div className={containerClasses}>
        <select id={id} className={selectClasses} {...props}>
          {children}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-gray-600 dark:text-gray-300">
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      {error && <p className={errorClasses}>{error}</p>}
    </div>
  );
};

export default Select;
