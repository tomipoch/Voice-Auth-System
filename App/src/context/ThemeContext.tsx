import { createContext, useEffect, useState, ReactNode } from 'react';
import { storageService } from '../services/storage';
import { applyTheme, getInitialTheme, getSystemTheme } from './theme';
import type { ThemeContextType } from '../types/index.js';

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => getInitialTheme());
  const [themeMode, setThemeMode] = useState<'light' | 'dark' | 'auto'>(() => {
    const saved = storageService.getThemePreference();
    return saved || 'light';
  });

  // Aplicar tema cuando cambia
  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  // Listener para cambios en el tema del sistema (solo si está en modo auto)
  useEffect(() => {
    if (themeMode !== 'auto') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      setTheme(e.matches ? 'dark' : 'light');
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [themeMode]);

  const toggleTheme = (): void => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    setThemeMode(newTheme);
    storageService.setThemePreference(newTheme);
  };

  const setThemePreference = (mode: 'light' | 'dark' | 'auto'): void => {
    setThemeMode(mode);

    if (mode === 'auto') {
      const systemTheme = getSystemTheme();
      setTheme(systemTheme);
      storageService.setItem('theme', 'auto');
    } else {
      setTheme(mode);
      storageService.setThemePreference(mode);
    }
  };

  const value: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme: setThemePreference,
    isDark: theme === 'dark',
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};
