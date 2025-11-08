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
    'block w-full px-3 py-2 border rounded-lg text-sm focus:ring-4 focus:outline-none transition-colors',
    error 
      ? 'border-red-300 text-red-900 placeholder-red-300 focus:ring-red-100 focus:border-red-500'
      : 'border-gray-300 text-gray-900 placeholder-gray-400 focus:ring-blue-100 focus:border-blue-500',
    className
  );

  return (
    <div className="space-y-1">
      {label && (
        <label 
          htmlFor={id} 
          className="block text-sm font-medium text-gray-700"
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
        <p className="text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
};

export default Input;