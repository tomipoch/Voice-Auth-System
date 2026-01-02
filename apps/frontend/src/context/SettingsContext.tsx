import { createContext, useState, useEffect, ReactNode } from 'react';
import { authStorage } from '../services/storage';

interface Settings {
  notifications?: {
    email?: boolean;
    push?: boolean;
    verificationAlerts?: boolean;
  };
  security?: {
    twoFactor?: boolean;
    sessionTimeout?: number;
    requireReauth?: boolean;
  };
  appearance?: {
    theme?: string;
    language?: string;
  };
}

interface SettingsContextType {
  settings: Settings;
  updateSettings: (newSettings: Settings) => void;
}

export const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const [settings, setSettings] = useState<Settings>({
    notifications: {
      email: true,
      push: false,
      verificationAlerts: true,
    },
    security: {
      twoFactor: false,
      sessionTimeout: 30,
      requireReauth: false,
    },
    appearance: {
      theme: 'system',
      language: 'es',
    },
  });

  // Load settings from user data if available
  useEffect(() => {
    const user = authStorage.getUser();
    if (user?.settings) {
      setSettings((prev) => ({
        ...prev,
        ...user.settings,
      }));
    }
  }, []);

  const updateSettings = (newSettings: Settings) => {
    setSettings(newSettings);
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};
