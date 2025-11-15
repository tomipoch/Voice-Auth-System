import { useContext } from 'react';
import { SettingsModalContext } from '../context/SettingsModalContext';

export const useSettingsModal = () => {
  const context = useContext(SettingsModalContext);
  if (!context) {
    throw new Error('useSettingsModal must be used within a SettingsModalProvider');
  }
  return context;
};