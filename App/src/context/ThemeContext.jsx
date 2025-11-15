import { createContext, useContext, useEffect, useState } from 'react';
import { storageService } from '../services/storage';

// Crear contexto del tema
const ThemeContext = createContext();

// Hook para usar el contexto
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme debe ser usado dentro de un ThemeProvider');
  }
  return context;
};

// Detectar preferencia del sistema
const getSystemTheme = () => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
};

// Aplicar tema al documento
const applyTheme = (theme) => {
  const root = document.documentElement;
  
  if (theme === 'dark') {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

// Provider del contexto
export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('light');
  const [mounted, setMounted] = useState(false);

  // Inicializar tema
  useEffect(() => {
    const savedTheme = storageService.getItem('theme');
    let initialTheme = savedTheme || 'auto';
    
    // Si es auto, usar preferencia del sistema
    if (initialTheme === 'auto') {
      initialTheme = getSystemTheme();
    }
    
    setTheme(initialTheme);
    applyTheme(initialTheme);
    setMounted(true);
  }, []);

  // Escuchar cambios en la preferencia del sistema
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e) => {
      const savedTheme = storageService.getItem('theme');
      if (savedTheme === 'auto' || !savedTheme) {
        const systemTheme = e.matches ? 'dark' : 'light';
        setTheme(systemTheme);
        applyTheme(systemTheme);
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Cambiar tema
  const changeTheme = (newTheme) => {
    let actualTheme = newTheme;
    
    // Si es auto, detectar tema del sistema
    if (newTheme === 'auto') {
      actualTheme = getSystemTheme();
    }
    
    setTheme(actualTheme);
    applyTheme(actualTheme);
    storageService.setItem('theme', newTheme);
  };

  // Toggle entre light y dark
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    changeTheme(newTheme);
  };

  // Obtener tema guardado (incluye 'auto')
  const getSavedTheme = () => {
    return storageService.getItem('theme') || 'auto';
  };

  const value = {
    theme,
    changeTheme,
    toggleTheme,
    getSavedTheme,
    mounted,
    isDark: theme === 'dark',
    isLight: theme === 'light',
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeProvider;