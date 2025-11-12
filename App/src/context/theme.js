export const getSystemTheme = () => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
};

export const applyTheme = (theme) => {
  if (typeof document === 'undefined') return;
  
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
    // Acceder directamente a localStorage sin el servicio para evitar dependencias circulares
    const saved = localStorage.getItem('voiceauth_theme_preference');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed === 'light' || parsed === 'dark') {
        return parsed;
      }
    }
    return getSystemTheme();
  } catch {
    return 'light';
  }
};
