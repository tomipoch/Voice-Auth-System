import { createContext, useEffect, useState, ReactNode } from 'react';
import { storageService } from '../services/storage';
import { applyTheme, getInitialTheme } from './theme';
import type { ThemeContextType } from '../types/index.js';

export const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider = ({ children }: ThemeProviderProps) => {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => getInitialTheme());

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = (): void => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    storageService.setThemePreference(newTheme);
  };

  const setThemeMode = (newTheme: 'light' | 'dark'): void => {
    setTheme(newTheme);
    storageService.setThemePreference(newTheme);
  };

  const value: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme: setThemeMode,
    isDark: theme === 'dark',
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};
