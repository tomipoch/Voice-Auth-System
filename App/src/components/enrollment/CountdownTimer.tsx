import { useEffect, useState } from 'react';

interface CountdownTimerProps {
  seconds?: number;
  onComplete: () => void;
  onTick?: (remaining: number) => void;
  className?: string;
}

const CountdownTimer = ({
  seconds = 3,
  onComplete,
  onTick,
  className = '',
}: CountdownTimerProps) => {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    if (remaining === 0) {
      onComplete();
      return;
    }

    const timer = setTimeout(() => {
      const newRemaining = remaining - 1;
      setRemaining(newRemaining);
      onTick?.(newRemaining);
    }, 1000);

    return () => clearTimeout(timer);
  }, [remaining, onComplete, onTick]);

  const getCountdownText = () => {
    if (remaining === 0) return '¡Ahora!';
    return remaining.toString();
  };

  const getCountdownColor = () => {
    if (remaining === 0) return 'text-green-600 dark:text-green-400';
    if (remaining === 1) return 'text-orange-600 dark:text-orange-400';
    return 'text-blue-600 dark:text-blue-400';
  };

  const getBackgroundColor = () => {
    if (remaining === 0) return 'bg-green-100 dark:bg-green-900/30';
    if (remaining === 1) return 'bg-orange-100 dark:bg-orange-900/30';
    return 'bg-blue-100 dark:bg-blue-900/30';
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div
        className={`w-32 h-32 rounded-full flex items-center justify-center ${getBackgroundColor()} transition-all duration-300 transform ${
          remaining === 0 ? 'scale-110' : 'scale-100'
        } animate-pulse`}
      >
        <span
          className={`text-6xl font-bold ${getCountdownColor()} transition-colors duration-300`}
        >
          {getCountdownText()}
        </span>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-4 font-medium">
        {remaining === 0 ? 'Comienza a leer' : 'Prepárate...'}
      </p>
    </div>
  );
};

export default CountdownTimer;
