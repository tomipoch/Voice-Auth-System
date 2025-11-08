import { clsx } from 'clsx';

const Card = ({ children, className = '', ...props }) => {
  const classes = clsx(
    'bg-white rounded-lg border border-gray-200 shadow-sm p-6',
    className
  );

  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardHeader = ({ children, className = '', ...props }) => {
  const classes = clsx('mb-4', className);
  
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
};

const CardTitle = ({ children, className = '', ...props }) => {
  const classes = clsx('text-xl font-semibold text-gray-900', className);
  
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