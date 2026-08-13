/**
 * AuthContext tests against the typed authService.
 *
 * The context now imports from services/authService (no longer
 * from the apiServices facade), and the dev-login shortcut has
 * been removed (Fase 5 item 3). These tests verify the
 * remaining public surface: initial state, restored state from
 * storage, successful/failed login, and logout.
 */

import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useContext } from 'react';
import { AuthProvider, AuthContext } from '../AuthContext';

vi.mock('../../services/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshToken: vi.fn(),
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));
vi.mock('../../services/storage', () => ({
  authStorage: {
    getAccessToken: vi.fn(),
    getRefreshToken: vi.fn(),
    setAccessToken: vi.fn(),
    setRefreshToken: vi.fn(),
    setUser: vi.fn(),
    getUser: vi.fn(),
    clearAuth: vi.fn(),
  },
}));
vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

const TestComponent = () => {
  const context = useContext(AuthContext);
  if (!context) return <div>No context</div>;

  const { user, isLoading, isAuthenticated, login, logout } = context;

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="user">{user ? (user as { email?: string }).email : 'No User'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'Yes' : 'No'}</div>
      <button
        onClick={() =>
          (login as (c: { email: string; password: string }) => Promise<unknown>)({
            email: 'test@example.com',
            password: 'Password1!',
          })
        }
      >
        Login
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

import { authService } from '../../services/authService';
import { authStorage } from '../../services/storage';

const mockedLogin = vi.mocked(authService.login);
const mockedLogout = vi.mocked(authService.logout);
const mockedGetProfile = vi.mocked(authService.getProfile);
const mockedGetAccessToken = vi.mocked(authStorage.getAccessToken);
const mockedGetUser = vi.mocked(authStorage.getUser);

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockedGetAccessToken.mockReturnValue(null);
    mockedGetUser.mockReturnValue(null);
  });

  it('provides initial state with no user', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('No');
    });
  });

  it('loads user from storage on mount', async () => {
    const storedUser = {
      id: '1',
      email: 'stored@example.com',
      name: 'Stored User',
      role: 'user' as const,
      created_at: '2024-01-01T00:00:00Z',
    };
    mockedGetAccessToken.mockReturnValue('stored-token');
    mockedGetUser.mockReturnValue(storedUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('stored@example.com');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Yes');
    });
  });

  it('handles successful login', async () => {
    mockedLogin.mockResolvedValue({
      access_token: 'new-token',
      token_type: 'bearer',
      expires_in: 7200,
      user: {
        id: '2',
        email: 'new@example.com',
        name: 'New User',
        role: 'user',
        created_at: '2024-01-01T00:00:00Z',
      },
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });

    await act(async () => {
      screen.getByText('Login').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('new@example.com');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Yes');
    });
  });

  it('handles login failure', async () => {
    mockedLogin.mockRejectedValue(
      Object.assign(new Error('Login failed'), {
        response: { data: { message: 'Invalid credentials' } },
      }),
    );

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });

    await act(async () => {
      screen.getByText('Login').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });
  });

  it('handles logout', async () => {
    const storedUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user' as const,
      created_at: '2024-01-01T00:00:00Z',
    };
    mockedGetAccessToken.mockReturnValue('token');
    mockedGetUser.mockReturnValue(storedUser);
    mockedLogout.mockResolvedValue(undefined);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
    });

    await act(async () => {
      screen.getByText('Logout').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('No');
    });
  });

  it('refreshes profile from server on mount when local token is present', async () => {
    const storedUser = {
      id: '1',
      email: 'test@example.com',
      name: 'Test User',
      role: 'user' as const,
      created_at: '2024-01-01T00:00:00Z',
    };
    const serverProfile = {
      ...storedUser,
      name: 'Server User',
      email: 'server@example.com',
    };
    mockedGetAccessToken.mockReturnValue('token');
    mockedGetUser.mockReturnValue(storedUser);
    mockedGetProfile.mockResolvedValue(serverProfile);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('server@example.com');
    });
  });
});
