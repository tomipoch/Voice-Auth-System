import { clsx } from 'clsx';

const Input = ({ 
  label,
  error,
  className = '',
  id,
  type = 'text',
  ...props 
}) => {
  const inputClasses = clsx(
    'block w-full px-4 py-3 rounded-xl text-sm focus:ring-2 focus:outline-none transition-all duration-300 backdrop-blur-sm font-medium',
    error 
      ? 'border-red-300/60 bg-red-50/80 text-red-900 placeholder-red-400 focus:ring-red-500/50 focus:border-red-500/60 shadow-sm'
      : 'border-blue-200/50 bg-white/80 text-gray-800 placeholder-gray-500 focus:ring-blue-500/50 focus:border-blue-500/60 shadow-sm hover:shadow-md border',
    className
  );

  const labelClasses = 'block text-sm font-medium text-gray-700 mb-2';
  const errorClasses = 'text-sm text-red-500 mt-1';

  return (
    <div className="space-y-1">
      {label && (
        <label 
          htmlFor={id} 
          className={labelClasses}
        >
          {label}
        </label>
      )}
      <input
        id={id}
        type={type}
        className={inputClasses}
        {...props}
      />
      {error && (
        <p className={errorClasses}>
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;