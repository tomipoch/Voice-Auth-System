import { createContext, useReducer, useEffect, ReactNode } from 'react';
import { authService } from '../services/authService';
import { authStorage } from '../services/storage';
import { features } from '../config/environment.js';
import toast from 'react-hot-toast';
import type { LoginCredentials, RegisterData, User } from '../types';

// ============================================
// Type Definitions
// ============================================

// AuthUser is unified with the shared User type from
// src/types/index.ts so the storage layer and consumers agree
// on a single shape.
type AuthUser = User;

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: AuthUser; token: string } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'SET_USER'; payload: AuthUser | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'CLEAR_ERROR' };

export interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<{ success: boolean; error?: string }>;
  register: (userData: RegisterData) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  clearError: () => void;
  refreshUser: () => Promise<{ success: boolean; error?: unknown }>;
}

// ============================================
// Initial State & Action Types
// ============================================

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

const actionTypes = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  SET_USER: 'SET_USER',
  SET_LOADING: 'SET_LOADING',
  CLEAR_ERROR: 'CLEAR_ERROR',
} as const;

// ============================================
// Reducer
// ============================================

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case actionTypes.LOGIN_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case actionTypes.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case actionTypes.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case actionTypes.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case actionTypes.SET_USER:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      };
    case actionTypes.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload,
      };
    case actionTypes.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

// ============================================
// Context
// ============================================

const AuthContext = createContext<AuthContextValue | null>(null);

// Provider del contexto
export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Inicializar autenticación al cargar la app
  useEffect(() => {
    const initAuth = async () => {
      dispatch({ type: actionTypes.SET_LOADING, payload: true });

      const token = authStorage.getAccessToken();
      const user = authStorage.getUser();

      if (features.debugMode) {
        console.log('🔍 Auth initialization check:', {
          hasToken: !!token,
          hasUser: !!user,
          token: token ? token.substring(0, 20) + '...' : 'none',
          user: user ? user.name : 'none',
        });
      }

      if (token && user) {
        try {
          // Verificar token con el servidor
          try {
            const profile = await authService.getProfile();
            dispatch({
              type: actionTypes.LOGIN_SUCCESS,
              payload: {
                user: profile,
                token,
              },
            });

            if (features.debugMode) {
              console.log('🔐 Server Auth initialized:', {
                user: profile.name,
                role: profile.role,
              });
            }
          } catch (error: unknown) {
            // Diferenciar tipos de error para mejor manejo
            const axiosError = error as { response?: { status?: number }; message?: string };
            if (axiosError.response?.status === 401) {
              // Token realmente inválido o expirado - limpiar sesión
              authStorage.clearAuth();
              dispatch({ type: actionTypes.LOGOUT });

              if (features.debugMode) {
                console.log('🔓 Invalid token cleared (401)');
              }
            } else {
              // Error de red o servidor temporal - MANTENER sesión local
              console.warn('⚠️ Error verificando token, usando datos locales:', axiosError.message);
              dispatch({
                type: actionTypes.LOGIN_SUCCESS,
                payload: {
                  user: user,
                  token,
                },
              });

              if (features.debugMode) {
                console.log('🔐 Auth initialized with local data (network error)');
              }

              // Intentar reconectar en background después de 5 segundos
              setTimeout(async () => {
                try {
                  const profile = await authService.getProfile();
                  // Actualizar con datos frescos del servidor
                  dispatch({
                    type: actionTypes.SET_USER,
                    payload: profile,
                  });
                  authStorage.setUser(profile);

                  if (features.debugMode) {
                    console.log('🔄 Profile refreshed from server');
                  }
                } catch {
                  // Silenciosamente fallar si aún no hay conexión
                  if (features.debugMode) {
                    console.log('⚠️ Background refresh failed, keeping local data');
                  }
                }
              }, 5000);
            }
          }
        } catch (error) {
          // Error crítico inesperado
          console.error('❌ Critical error in initAuth:', error);
          dispatch({ type: actionTypes.SET_LOADING, payload: false });
        }
      } else {
        dispatch({ type: actionTypes.SET_LOADING, payload: false });
      }
    };

    initAuth();
  }, []);

  // Sincronización entre pestañas
  useEffect(() => {
    // Track if we're in the middle of a login/logout to avoid race conditions
    let debounceTimer: NodeJS.Timeout | null = null;

    const handleStorageChange = (e: StorageEvent) => {
      // IMPORTANT: storage events should only fire for OTHER tabs/windows
      // If e.storageArea is null or the event is from this window, ignore it
      if (!e.storageArea) {
        return;
      }

      // Clear any pending debounce
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }

      // Debounce storage changes to avoid race conditions during login
      debounceTimer = setTimeout(() => {
        // Detectar logout en otra pestaña
        if (e.key === 'voiceauth_logout_signal') {
          authStorage.clearAuth();
          dispatch({ type: actionTypes.LOGOUT });

          if (features.debugMode) {
            console.log('🔓 Logout detected from another tab');
          }

          toast('Sesión cerrada en otra pestaña', { icon: 'ℹ️' });
          window.location.href = '/login';
        }

        // Detectar login en otra pestaña
        if (e.key === 'voiceauth_login_signal') {
          const token = authStorage.getAccessToken();
          const user = authStorage.getUser();

          if (token && user && !state.isAuthenticated) {
            dispatch({
              type: actionTypes.LOGIN_SUCCESS,
              payload: { user, token },
            });

            if (features.debugMode) {
              console.log('🔐 Login detected from another tab');
            }

            toast('Sesión iniciada en otra pestaña', { icon: 'ℹ️' });
          }
        }

        // Detectar cambios directos en token/user
        const tokenKey = 'voiceauth_voiceauth_token'; // Use the actual key
        if (e.key === tokenKey || e.key === 'voiceauth_voiceauth_user') {
          const newToken = authStorage.getAccessToken();
          const newUser = authStorage.getUser();

          if (!newToken || !newUser) {
            // Se eliminó el token/user
            if (state.isAuthenticated) {
              if (features.debugMode) {
                console.log('🔓 Token/user removed in another tab, logging out');
              }
              dispatch({ type: actionTypes.LOGOUT });
            }
          } else if (!state.isAuthenticated) {
            // Se agregó token/user
            dispatch({
              type: actionTypes.LOGIN_SUCCESS,
              payload: { user: newUser, token: newToken },
            });
          }
        }
      }, 100); // 100ms debounce
    };

    window.addEventListener('storage', handleStorageChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
    };
  }, [state.isAuthenticated]);

  // Función de login
  const login = async (credentials: LoginCredentials) => {
    try {
      dispatch({ type: actionTypes.LOGIN_START });

      // Login contra el backend
      const response = await authService.login(credentials);

      // La respuesta viene como: { access_token, refresh_token, user, token_type, expires_in }
      const { user, access_token, refresh_token } = response;

      // El servicio ya persiste tokens y usuario en authStorage
      // pero guardamos el refresh_token si viene (defensa redundante)
      // para no perderlo entre upgrades del servicio.
      if (refresh_token) {
        authStorage.setRefreshToken(refresh_token);
      }

      dispatch({
        type: actionTypes.LOGIN_SUCCESS,
        payload: { user, token: access_token },
      });

      // Notificar a otras pestañas sobre el login
      localStorage.setItem('voiceauth_login_signal', Date.now().toString());
      localStorage.removeItem('voiceauth_login_signal');

      if (features.debugMode) {
        console.log('🔐 Server login successful:', { user: user.name, role: user.role });
      }
      toast.success(`¡Bienvenido, ${user.name}!`);
      return { success: true };
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { message?: string } } };
      const errorMessage = axiosError.response?.data?.message || 'Error al iniciar sesión';
      dispatch({
        type: actionTypes.LOGIN_FAILURE,
        payload: errorMessage,
      });

      if (features.debugMode) {
        console.error('❌ Login failed:', error);
      }
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Función de registro
  const register = async (userData: RegisterData) => {
    try {
      dispatch({ type: actionTypes.LOGIN_START });

      await authService.register(userData);
      toast.success('Usuario registrado exitosamente. Puedes iniciar sesión.');

      dispatch({ type: actionTypes.SET_LOADING, payload: false });
      return { success: true };
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { message?: string } } };
      const errorMessage = axiosError.response?.data?.message || 'Error al registrar usuario';
      dispatch({
        type: actionTypes.LOGIN_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    }
  };

  // Función de logout
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      if (features.debugMode) {
        console.error('❌ Error during logout:', error);
      }
    } finally {
      // Notificar a otras pestañas sobre el logout
      localStorage.setItem('voiceauth_logout_signal', Date.now().toString());
      localStorage.removeItem('voiceauth_logout_signal');

      // Limpiar usando authStorage
      authStorage.clearAuth();
      dispatch({ type: actionTypes.LOGOUT });

      if (features.debugMode) {
        console.log('🔓 User logged out');
      }
      toast.success('Sesión cerrada exitosamente');
    }
  };

  // Limpiar errores
  const clearError = () => {
    dispatch({ type: actionTypes.CLEAR_ERROR });
  };

  // Actualizar datos del usuario
  const refreshUser = async () => {
    try {
      const profile = await authService.getProfile();
      dispatch({
        type: actionTypes.SET_USER,
        payload: profile,
      });
      // Actualizar también en storage local para persistencia inmediata
      authStorage.setUser(profile);
      return { success: true };
    } catch (error) {
      console.error('Error refreshing user:', error);
      return { success: false, error };
    }
  };

  const value = {
    ...state,
    login,
    register,
    logout,
    clearError,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Exportar el contexto para que pueda ser importado en el hook
export { AuthContext };
