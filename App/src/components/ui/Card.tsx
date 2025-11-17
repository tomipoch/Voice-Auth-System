import { clsx } from 'clsx';
import type { HTMLAttributes, ReactNode } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'glass' | 'solid';
}

interface CardChildProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  className?: string;
}

const Card = ({ children, className = '', variant = 'default', ...props }: CardProps) => {
  const baseClasses =
    'rounded-2xl shadow-xl backdrop-blur-xl transition-all duration-300 hover:shadow-2xl';

  const variantClasses = {
    default:
      'bg-white dark:bg-gray-900/70 dark:bg-gray-800/70 border border-blue-200/40 dark:border-gray-600/40 p-6',
    glass:
      'bg-white dark:bg-gray-900/60 dark:bg-gray-800/60 border border-blue-200/30 dark:border-gray-600/30 p-8',
    solid:
      'bg-white dark:bg-gray-900 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 dark:border-gray-700 p-6 shadow-lg',
  };

  const classes = clsx(baseClasses, variantClasses[variant], className);

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardHeader = ({ children, className = '', ...props }: CardChildProps) => {
  const classes = clsx('mb-6', className);

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardTitle = ({ children, className = '', ...props }: CardChildProps) => {
  const classes = clsx(
    'text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent',
    className
  );

  return (
    <h3 className={classes} {...props}>
      {children}
    </h3>
  );
};

const CardContent = ({ children, className = '', ...props }: CardChildProps) => {
  return (
    <div className={className} {...props}>
      {children}
    </div>
  );
};

Card.Header = CardHeader;
Card.Title = CardTitle;
Card.Content = CardContent;

export default Card;
