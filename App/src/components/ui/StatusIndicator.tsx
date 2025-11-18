import { CheckCircle, XCircle, AlertCircle, Clock, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import type { LucideIcon } from 'lucide-react';

export type StatusType = 'success' | 'error' | 'warning' | 'pending' | 'loading';

interface StatusIndicatorProps {
  status: StatusType;
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

interface StatusConfig {
  icon: LucideIcon;
  className: string;
  iconClassName: string;
}

const StatusIndicator = ({ status, message, size = 'md' }: StatusIndicatorProps) => {
  const getStatusConfig = (status: StatusType): StatusConfig => {
    switch (status) {
      case 'success':
        return {
          icon: CheckCircle,
          className: 'text-green-500 bg-green-50 border-green-200',
          iconClassName: 'text-green-600',
        };
      case 'error':
        return {
          icon: XCircle,
          className: 'text-red-500 bg-red-50 border-red-200',
          iconClassName: 'text-red-600',
        };
      case 'warning':
        return {
          icon: AlertCircle,
          className: 'text-yellow-500 bg-yellow-50 border-yellow-200',
          iconClassName: 'text-yellow-600',
        };
      case 'pending':
        return {
          icon: Clock,
          className: 'text-blue-500 bg-blue-50 border-blue-200',
          iconClassName: 'text-blue-600',
        };
      case 'loading':
        return {
          icon: Loader2,
          className: 'text-blue-500 bg-blue-50 border-blue-200',
          iconClassName: 'text-blue-600 animate-spin',
        };
      default:
        return {
          icon: AlertCircle,
          className:
            'text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
          iconClassName: 'text-gray-600 dark:text-gray-400',
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'p-2 text-xs',
    md: 'p-3 text-sm',
    lg: 'p-4 text-base',
  };

  const iconSizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  return (
    <div className={clsx('rounded-lg border', config.className, sizeClasses[size])}>
      <div className="flex items-center space-x-2">
        <Icon className={clsx(iconSizes[size], config.iconClassName)} />
        {message && <span className="font-medium">{message}</span>}
      </div>
    </div>
  );
};

export default StatusIndicator;
