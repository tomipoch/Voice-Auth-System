import { useEffect, useState } from 'react';
import { WifiOff } from 'lucide-react';
import toast from 'react-hot-toast';

/**
 * Componente que muestra el estado de conexión a internet
 * y notifica al usuario cuando pierde/recupera la conexión
 */
export const ConnectionStatus = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    let toastId: string | undefined;

    const handleOnline = () => {
      setIsOnline(true);
      setShowBanner(false);
      
      // Limpiar toast de offline si existe
      if (toastId) {
        toast.dismiss(toastId);
      }
      
      toast.success('Conexión restaurada', {
        icon: '🟢',
        duration: 3000,
      });
    };

    const handleOffline = () => {
      setIsOnline(false);
      setShowBanner(true);
      
      toastId = toast.error('Sin conexión a internet', {
        icon: '🔴',
        duration: Infinity,
      });
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Verificar estado inicial
    if (!navigator.onLine) {
      handleOffline();
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (toastId) {
        toast.dismiss(toastId);
      }
    };
  }, []);

  // No mostrar banner si está online
  if (!showBanner || isOnline) return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 bg-red-500 text-white py-2 px-4 text-center z-50 flex items-center justify-center gap-2 shadow-lg"
      role="alert"
      aria-live="assertive"
    >
      <WifiOff className="w-4 h-4" aria-hidden="true" />
      <span className="text-sm font-medium">Sin conexión - Usando datos locales</span>
    </div>
  );
};

export default ConnectionStatus;
