import { useContext } from 'react';
import { AuthContext, type AuthContextValue } from '../context/AuthContext';

// Hook para usar el contexto de autenticación
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};
