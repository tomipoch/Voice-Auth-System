import { createContext, useReducer, useEffect } from 'react';
import { authService } from '../services/apiServices';
import { authStorage } from '../services/storage';
import { features } from '../config/environment.js';
import toast from 'react-hot-toast';

// Estado inicial
const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Tipos de acciones
const actionTypes = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  SET_USER: 'SET_USER',
  SET_LOADING: 'SET_LOADING',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer
const authReducer = (state, action) => {
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

// Crear contexto
const AuthContext = createContext(null);

// Provider del contexto
export const AuthProvider = ({ children }) => {
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
          // En desarrollo, si es un token dev, no verificar con servidor
          if (token.startsWith('dev-token-') || token.startsWith('admin-token-')) {
            dispatch({
              type: actionTypes.LOGIN_SUCCESS,
              payload: {
                user: user,
                token,
              },
            });

            if (features.debugMode) {
              console.log('🔐 Dev Auth initialized (skip server verification):', {
                user: user.name,
                role: user.role,
              });
            }
          } else {
            // Verificar token con el servidor para tokens reales
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
          }
        } catch {
          // Token inválido, limpiar storage
          authStorage.clearAuth();
          dispatch({ type: actionTypes.LOGOUT });

          if (features.debugMode) {
            console.log('🔓 Invalid token cleared');
          }
        }
      } else {
        dispatch({ type: actionTypes.SET_LOADING, payload: false });
      }
    };

    initAuth();
  }, []);

  // Función de login
  const login = async (credentials) => {
    try {
      dispatch({ type: actionTypes.LOGIN_START });

      // Usuario de desarrollo especial
      if (credentials.email === 'dev@test.com' && credentials.password === '123456') {
        const devUser = {
          id: 'dev-user-1',
          name: 'Usuario Desarrollo',
          email: 'dev@test.com',
          role: 'user',
        };
        const devToken = 'dev-token-' + Date.now();

        // Guardar usando authStorage
        authStorage.setAccessToken(devToken);
        authStorage.setUser(devUser);

        if (features.debugMode) {
          console.log('💾 Dev login - Data saved to storage:', {
            token: devToken.substring(0, 20) + '...',
            user: devUser.name,
          });
        }

        dispatch({
          type: actionTypes.LOGIN_SUCCESS,
          payload: { user: devUser, token: devToken },
        });

        if (features.debugMode) {
          console.log('🔐 Dev login successful:', devUser);
        }
        toast.success(`¡Bienvenido, ${devUser.name}! (Modo desarrollo)`);
        return { success: true };
      }

      // Usuario admin de desarrollo
      if (credentials.email === 'admin@test.com' && credentials.password === '123456') {
        const adminUser = {
          id: 'admin-user-1',
          name: 'Admin Desarrollo',
          email: 'admin@test.com',
          role: 'admin',
        };
        const adminToken = 'admin-token-' + Date.now();

        // Guardar usando authStorage
        authStorage.setAccessToken(adminToken);
        authStorage.setUser(adminUser);

        dispatch({
          type: actionTypes.LOGIN_SUCCESS,
          payload: { user: adminUser, token: adminToken },
        });

        toast.success(`¡Bienvenido, ${adminUser.name}! (Admin - Modo desarrollo)`);
        return { success: true };
      }

      // Login normal con el servidor
      const response = await authService.login(credentials);
      const { user, token } = response;

      // Guardar usando authStorage
      authStorage.setAccessToken(token);
      authStorage.setUser(user);

      dispatch({
        type: actionTypes.LOGIN_SUCCESS,
        payload: { user, token },
      });

      if (features.debugMode) {
        console.log('🔐 Server login successful:', { user: user.name, role: user.role });
      }
      toast.success(`¡Bienvenido, ${user.name}!`);
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Error al iniciar sesión';
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
  const register = async (userData) => {
    try {
      dispatch({ type: actionTypes.LOGIN_START });

      await authService.register(userData);
      toast.success('Usuario registrado exitosamente. Puedes iniciar sesión.');

      dispatch({ type: actionTypes.SET_LOADING, payload: false });
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Error al registrar usuario';
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

  const value = {
    ...state,
    login,
    register,
    logout,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Exportar el contexto para que pueda ser importado en el hook
export { AuthContext };
