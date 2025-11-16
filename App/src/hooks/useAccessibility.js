import { useEffect, useCallback } from 'react';

/**
 * Hook para gestión de navegación por teclado
 * Proporciona utilidades para mejorar la accesibilidad del teclado
 */
export const useKeyboardNavigation = () => {
  // Trap focus dentro de un elemento (útil para modales)
  const trapFocus = useCallback((element) => {
    if (!element) return;

    const focusableElements = element.querySelectorAll(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        // Tab + Shift (hacia atrás)
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        // Tab (hacia adelante)
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    element.addEventListener('keydown', handleTabKey);

    // Focus en el primer elemento
    firstElement?.focus();

    return () => {
      element.removeEventListener('keydown', handleTabKey);
    };
  }, []);

  // Restaurar foco al cerrar modal
  const restoreFocus = useCallback((previousElement) => {
    if (previousElement && previousElement.focus) {
      previousElement.focus();
    }
  }, []);

  return {
    trapFocus,
    restoreFocus,
  };
};

/**
 * Hook para anunciar cambios a lectores de pantalla
 */
export const useAnnounce = () => {
  const announce = useCallback((message, priority = 'polite') => {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;

    document.body.appendChild(announcement);

    // Remover después de que se haya anunciado
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  }, []);

  return { announce };
};

/**
 * Hook para gestionar focus visible (solo mostrar outline con teclado)
 */
export const useFocusVisible = () => {
  useEffect(() => {
    let hadKeyboardEvent = false;

    const onKeyDown = () => {
      hadKeyboardEvent = true;
    };

    const onPointerDown = () => {
      hadKeyboardEvent = false;
    };

    const onFocus = (e) => {
      if (hadKeyboardEvent) {
        e.target.classList.add('focus-visible');
      }
    };

    const onBlur = (e) => {
      e.target.classList.remove('focus-visible');
    };

    document.addEventListener('keydown', onKeyDown, true);
    document.addEventListener('pointerdown', onPointerDown, true);
    document.addEventListener('focus', onFocus, true);
    document.addEventListener('blur', onBlur, true);

    return () => {
      document.removeEventListener('keydown', onKeyDown, true);
      document.removeEventListener('pointerdown', onPointerDown, true);
      document.removeEventListener('focus', onFocus, true);
      document.removeEventListener('blur', onBlur, true);
    };
  }, []);
};

/**
 * Hook para detectar modo de alto contraste
 */
export const useHighContrastMode = () => {
  const isHighContrast =
    window.matchMedia('(prefers-contrast: high)').matches ||
    window.matchMedia('(-ms-high-contrast: active)').matches;

  return isHighContrast;
};
