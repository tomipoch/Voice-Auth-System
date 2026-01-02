import { useEffect, ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  size?: 'small' | 'medium' | 'large' | 'xl';
  className?: string;
}

const Modal = ({
  isOpen,
  onClose,
  children,
  title,
  size = 'large',
  className = '',
}: ModalProps) => {
  // Cerrar modal con Escape
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden'; // Prevenir scroll del body
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    small: 'max-w-md',
    medium: 'max-w-2xl',
    large: 'max-w-4xl',
    xl: 'max-w-6xl',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop con animación mejorada */}
      <div
        className="fixed inset-0 transition-all duration-300 ease-in-out"
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(59, 130, 246, 0.15) 0%, rgba(0, 0, 0, 0.4) 70%)',
          backdropFilter: 'blur(8px)',
        }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Container con animación mejorada */}
      <div className="flex min-h-full items-center justify-center p-4 sm:p-6">
        <div
          className={`
            relative w-full ${sizeClasses[size]} 
            transform transition-all duration-300 ease-out
            ${className}
          `}
          style={{
            animation: isOpen ? 'modalSlideIn 0.3s ease-out' : undefined,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Modal principal con estilo liquid glass mejorado */}
          <div
            className="relative overflow-hidden rounded-3xl shadow-2xl bg-white dark:bg-gray-800/95 border border-white/30 dark:border-gray-600/30 backdrop-blur-[20px]"
            style={{
              boxShadow: `
                0 25px 50px -12px rgba(0, 0, 0, 0.25),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6)
              `,
            }}
          >
            {/* Elementos decorativos de fondo */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div
                className="absolute -top-40 -right-40 w-80 h-80 rounded-full opacity-20"
                style={{
                  background: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
                  filter: 'blur(60px)',
                }}
              />
              <div
                className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full opacity-20"
                style={{
                  background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)',
                  filter: 'blur(60px)',
                }}
              />
            </div>

            {/* Header mejorado */}
            {title && (
              <div className="relative flex items-center justify-between p-6 border-b border-white/20 dark:border-gray-600/20">
                <h2 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-purple-800 dark:from-gray-200 dark:via-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
                  {title}
                </h2>
                <button
                  onClick={onClose}
                  className="group relative p-2 hover:bg-white dark:bg-gray-900/20 dark:hover:bg-gray-700/20 rounded-xl transition-all duration-200 backdrop-blur-sm"
                >
                  <X className="h-6 w-6 text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 transition-colors" />
                  <div className="absolute inset-0 rounded-xl bg-white dark:bg-gray-700/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              </div>
            )}

            {/* Content con padding mejorado */}
            <div className={`relative ${title ? 'p-6' : 'p-8'}`}>{children}</div>
          </div>
        </div>
      </div>

      {/* Estilos CSS en línea para animaciones */}
      <style>{`
        @keyframes modalSlideIn {
          0% {
            opacity: 0;
            transform: translate3d(0, -20px, 0) scale(0.95);
          }
          100% {
            opacity: 1;
            transform: translate3d(0, 0, 0) scale(1);
          }
        }
      `}</style>
    </div>
  );
};

export default Modal;
