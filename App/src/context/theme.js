import { storageService } from '../services/storage';

export const getSystemTheme = () => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
};

export const applyTheme = (theme) => {
  const root = document.documentElement;
  const body = document.body;
  
  if (theme === 'dark') {
    root.classList.add('dark');
    root.style.colorScheme = 'dark';
    body.style.colorScheme = 'dark';
  } else {
    root.classList.remove('dark');
    root.style.colorScheme = 'light';
    body.style.colorScheme = 'light';
  }
};

export const getInitialTheme = () => {
  if (typeof window === 'undefined') return 'light';
  
  try {
    const saved = storageService.getThemePreference();
    if (saved && (saved === 'light' || saved === 'dark')) {
      return saved;
    }
    return getSystemTheme();
  } catch {
    return 'light';
  }
};
