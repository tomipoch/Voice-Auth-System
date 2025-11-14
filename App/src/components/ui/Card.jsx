import { clsx } from 'clsx';

const Card = ({ children, className = '', variant = 'default', ...props }) => {
  const baseClasses = 'rounded-2xl shadow-xl backdrop-blur-xl transition-all duration-300 hover:shadow-2xl';
  
  const variantClasses = {
    default: 'bg-white/70 border border-blue-200/40 p-6',
    glass: 'bg-white/60 border border-blue-200/30 p-8',
    solid: 'bg-white border border-gray-200 p-6 shadow-lg',
  };
  
  const classes = clsx(
    baseClasses,
    variantClasses[variant],
    className
  );

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardHeader = ({ children, className = '', ...props }) => {
  const classes = clsx('mb-6', className);
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardTitle = ({ children, className = '', ...props }) => {
  const classes = clsx(
    'text-2xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent', 
    className
  );
  
  return (
    <h3 className={classes} {...props}>
      {children}
    </h3>
  );
};

const CardContent = ({ children, className = '', ...props }) => {
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