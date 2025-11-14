import { createContext, useReducer, useEffect } from 'react';
import { authService } from '../services/apiServices';
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
      
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');

      if (token && user) {
        try {
          // Verificar token con el servidor
          const profile = await authService.getProfile();
          dispatch({
            type: actionTypes.LOGIN_SUCCESS,
            payload: {
              user: profile,
              token,
            },
          });
        } catch {
          // Token inválido, limpiar localStorage
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          dispatch({ type: actionTypes.LOGOUT });
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
          role: 'user'
        };
        const devToken = 'dev-token-' + Date.now();

        // Guardar en localStorage
        localStorage.setItem('token', devToken);
        localStorage.setItem('user', JSON.stringify(devUser));

        dispatch({
          type: actionTypes.LOGIN_SUCCESS,
          payload: { user: devUser, token: devToken },
        });

        toast.success(`¡Bienvenido, ${devUser.name}! (Modo desarrollo)`);
        return { success: true };
      }

      // Usuario admin de desarrollo
      if (credentials.email === 'admin@test.com' && credentials.password === '123456') {
        const adminUser = {
          id: 'admin-user-1',
          name: 'Admin Desarrollo',
          email: 'admin@test.com',
          role: 'admin'
        };
        const adminToken = 'admin-token-' + Date.now();

        // Guardar en localStorage
        localStorage.setItem('token', adminToken);
        localStorage.setItem('user', JSON.stringify(adminUser));

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

      // Guardar en localStorage
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));

      dispatch({
        type: actionTypes.LOGIN_SUCCESS,
        payload: { user, token },
      });

      toast.success(`¡Bienvenido, ${user.name}!`);
      return { success: true };
    } catch (error) {
      const errorMessage = error.response?.data?.message || 'Error al iniciar sesión';
      dispatch({
        type: actionTypes.LOGIN_FAILURE,
        payload: errorMessage,
      });
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
      console.error('Error during logout:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      dispatch({ type: actionTypes.LOGOUT });
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

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Exportar el contexto para que pueda ser importado en el hook
export { AuthContext };