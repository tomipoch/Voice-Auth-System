import { useContext } from 'react';
import { SettingsModalContext } from '../context/SettingsModalContext';
import type { SettingsModalContextType } from '../types/index.js';

export const useSettingsModal = (): SettingsModalContextType => {
  const context = useContext(SettingsModalContext);
  if (!context) {
    throw new Error('useSettingsModal must be used within a SettingsModalProvider');
  }
  return context;
};
