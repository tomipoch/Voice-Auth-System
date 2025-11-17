import { createContext, useState, ReactNode } from 'react';
import type { SettingsModalContextType } from '../types/index.js';

const SettingsModalContext = createContext<SettingsModalContextType | undefined>(undefined);

export const SettingsModalProvider = ({ children }: { children: ReactNode }) => {
  const [isOpen, setIsOpen] = useState(false);

  const openModal = () => setIsOpen(true);
  const closeModal = () => setIsOpen(false);

  const value: SettingsModalContextType = {
    isOpen,
    openModal,
    closeModal,
  };

  return <SettingsModalContext.Provider value={value}>{children}</SettingsModalContext.Provider>;
};

export { SettingsModalContext };
