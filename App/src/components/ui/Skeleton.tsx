interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

const Skeleton = ({
  className = '',
  variant = 'rectangular',
  width,
  height,
  animation = 'pulse',
}: SkeletonProps) => {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';

  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-none',
    rounded: 'rounded-xl',
  };

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'skeleton',
    none: '',
  };

  const style = {
    width: width ? (typeof width === 'number' ? `${width}px` : width) : '100%',
    height: height ? (typeof height === 'number' ? `${height}px` : height) : undefined,
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${animationClasses[animation]} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
};

// Preset skeleton components for common use cases
export const SkeletonText = ({
  lines = 3,
  className = '',
}: {
  lines?: number;
  className?: string;
}) => (
  <div className={`space-y-2 ${className}`}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} variant="text" width={i === lines - 1 ? '80%' : '100%'} />
    ))}
  </div>
);

export const SkeletonCard = ({ className = '' }: { className?: string }) => (
  <div
    className={`p-6 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 ${className}`}
  >
    <div className="flex items-center mb-4">
      <Skeleton variant="circular" width={48} height={48} className="mr-4" />
      <div className="flex-1">
        <Skeleton variant="text" width="60%" className="mb-2" />
        <Skeleton variant="text" width="40%" />
      </div>
    </div>
    <SkeletonText lines={3} />
  </div>
);

export const SkeletonTable = ({
  rows = 5,
  className = '',
}: {
  rows?: number;
  className?: string;
}) => (
  <div className={`space-y-3 ${className}`}>
    <Skeleton variant="rounded" height={40} className="mb-4" />
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} variant="rounded" height={60} />
    ))}
  </div>
);

export const SkeletonDashboard = () => (
  <div className="space-y-6">
    {/* Header */}
    <div className="mb-8">
      <Skeleton variant="text" width="40%" height={40} className="mb-2" />
      <Skeleton variant="text" width="60%" height={24} />
    </div>

    {/* Stats Grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>

    {/* Content Area */}
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <SkeletonCard />
      </div>
      <div>
        <SkeletonCard />
      </div>
    </div>
  </div>
);

// Skeleton for Login/Register pages (no sidebar)
export const SkeletonAuth = () => (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
    <div className="w-full max-w-md p-8">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 space-y-6">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <Skeleton variant="circular" width={64} height={64} />
        </div>

        {/* Title */}
        <Skeleton variant="text" width="60%" height={32} className="mx-auto mb-2" />
        <Skeleton variant="text" width="80%" height={20} className="mx-auto mb-6" />

        {/* Form fields */}
        <div className="space-y-4">
          <Skeleton variant="rounded" height={48} />
          <Skeleton variant="rounded" height={48} />
          <Skeleton variant="rounded" height={48} />
        </div>

        {/* Button */}
        <Skeleton variant="rounded" height={48} className="mt-6" />

        {/* Footer link */}
        <Skeleton variant="text" width="70%" height={16} className="mx-auto mt-4" />
      </div>
    </div>
  </div>
);

// Skeleton for pages with sidebar (Profile, Settings, etc.)
export const SkeletonPage = () => (
  <div className="space-y-6">
    <div className="mb-8">
      <Skeleton variant="text" width="30%" height={36} className="mb-2" />
      <Skeleton variant="text" width="50%" height={20} />
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <SkeletonCard />
        <SkeletonCard />
      </div>
      <div>
        <SkeletonCard />
      </div>
    </div>
  </div>
);

export default Skeleton;
