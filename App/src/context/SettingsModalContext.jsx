import React, { createContext, useState } from 'react';

const SettingsModalContext = createContext();

export const SettingsModalProvider = ({ children }) => {
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);

  const openSettingsModal = () => setIsSettingsModalOpen(true);
  const closeSettingsModal = () => setIsSettingsModalOpen(false);
  const toggleSettingsModal = () => setIsSettingsModalOpen((prev) => !prev);

  const value = {
    isSettingsModalOpen,
    openSettingsModal,
    closeSettingsModal,
    toggleSettingsModal,
  };

  return <SettingsModalContext.Provider value={value}>{children}</SettingsModalContext.Provider>;
};

export { SettingsModalContext };
