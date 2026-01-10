import { useEffect, useRef, useCallback } from 'react';
import { useAuth } from './useAuth';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

/**
 * Hook to handle automatic session timeout based on user inactivity
 * Monitors user activity and logs out after configured timeout period
 */
export const useSessionTimeout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const warningTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(0);

  useEffect(() => {
    if (lastActivityRef.current === 0) {
      lastActivityRef.current = Date.now();
    }
  }, []);

  // Get session timeout from user settings (in minutes)
  const sessionTimeout = user?.settings?.security?.sessionTimeout || 30;
  const timeoutMs = sessionTimeout * 60 * 1000; // Convert to milliseconds
  const warningMs = timeoutMs - 60 * 1000; // Show warning 1 minute before timeout

  const handleLogout = useCallback(async () => {
    toast.error('Sesión cerrada por inactividad');
    await logout();
    navigate('/login');
  }, [logout, navigate]);

  const showWarning = useCallback(() => {
    toast('Tu sesión expirará en 1 minuto por inactividad', {
      icon: '⚠️',
      duration: 60000, // Show for 1 minute
    });
  }, []);

  const resetTimer = useCallback(() => {
    lastActivityRef.current = Date.now();

    // Clear existing timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
    }

    // Set warning timer (1 minute before logout)
    if (warningMs > 0) {
      warningTimeoutRef.current = setTimeout(showWarning, warningMs);
    }

    // Set logout timer
    timeoutRef.current = setTimeout(handleLogout, timeoutMs);
  }, [timeoutMs, warningMs, handleLogout, showWarning]);

  useEffect(() => {
    // Only run if user is logged in
    if (!user) return;

    // Events that indicate user activity
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    // Throttle activity detection to avoid too many resets
    let throttleTimeout: NodeJS.Timeout | null = null;
    const handleActivity = () => {
      if (throttleTimeout) return;

      throttleTimeout = setTimeout(() => {
        resetTimer();
        throttleTimeout = null;
      }, 1000); // Throttle to once per second
    };

    // Add event listeners
    events.forEach((event) => {
      window.addEventListener(event, handleActivity);
    });

    // Initialize timer
    resetTimer();

    // Cleanup
    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (warningTimeoutRef.current) {
        clearTimeout(warningTimeoutRef.current);
      }
      if (throttleTimeout) {
        clearTimeout(throttleTimeout);
      }
    };
  }, [user, resetTimer]);

  return {
    sessionTimeout,
    lastActivity: lastActivityRef.current,
    resetTimer,
  };
};
