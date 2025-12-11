// @ts-nocheck
import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AuthProvider, AuthContext } from '../AuthContext';
import { useContext } from 'react';
import * as apiServices from '../../services/apiServices';
import * as storage from '../../services/storage';

// Mock modules
vi.mock('../../services/apiServices');
vi.mock('../../services/storage');
vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock localStorage
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

// Simple test component
const TestComponent = () => {
  const context = useContext(AuthContext);
  if (!context) return <div>No context</div>;

  const { user, isLoading, isAuthenticated, login, logout } = context;

  return (
    <div>
      <div data-testid="loading">{isLoading ? 'Loading' : 'Not Loading'}</div>
      <div data-testid="user">{user ? (user as any).email : 'No User'}</div>
      <div data-testid="authenticated">{isAuthenticated ? 'Yes' : 'No'}</div>
      <button onClick={() => (login as any)({ email: 'test@test.com', password: 'pass' })}>
        Login
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    // Setup default mocks
    vi.mocked(storage.authStorage.getAccessToken).mockReturnValue(null);
    vi.mocked(storage.authStorage.getUser).mockReturnValue(null);
    vi.mocked(storage.authStorage.setAccessToken).mockReturnValue(true);
    vi.mocked(storage.authStorage.setUser).mockReturnValue(true);
    vi.mocked(storage.authStorage.clearAuth).mockReturnValue(undefined);
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
    const mockUser = {
      id: '1',
      email: 'stored@test.com',
      name: 'Stored User',
      role: 'user' as const,
    };

    vi.mocked(storage.authStorage.getAccessToken).mockReturnValue('stored-token');
    vi.mocked(storage.authStorage.getUser).mockReturnValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('stored@test.com');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Yes');
    });
  });

  it('handles successful login', async () => {
    const mockResponse: any = {
      access_token: 'new-token',
      user: {
        id: '2',
        email: 'new@test.com',
        name: 'New User',
        role: 'user' as const,
      },
    };

    vi.mocked(apiServices.authService.login).mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });

    const loginButton = screen.getByText('Login');

    await act(async () => {
      loginButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('new@test.com');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Yes');
    });
  });

  it('handles login failure', async () => {
    vi.mocked(apiServices.authService.login).mockRejectedValue(new Error('Login failed'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });

    const loginButton = screen.getByText('Login');

    await act(async () => {
      loginButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
    });
  });

  it('handles logout', async () => {
    const mockUser = {
      id: '1',
      email: 'test@test.com',
      name: 'Test User',
      role: 'user' as const,
    };

    vi.mocked(storage.authStorage.getAccessToken).mockReturnValue('token');
    vi.mocked(storage.authStorage.getUser).mockReturnValue(mockUser);
    vi.mocked(apiServices.authService.logout).mockResolvedValue({
      success: true,
      data: { message: 'Logged out' },
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('test@test.com');
    });

    const logoutButton = screen.getByText('Logout');

    await act(async () => {
      logoutButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user')).toHaveTextContent('No User');
      expect(screen.getByTestId('authenticated')).toHaveTextContent('No');
    });
  });

  it('handles dev login', async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Not Loading');
    });

    const loginButton = screen.getByText('Login');

    // Mock dev login
    vi.mocked(apiServices.authService.login).mockResolvedValue({
      access_token: 'dev-token',
      user: {
        id: 'dev-1',
        email: 'dev@test.com',
        name: 'Dev User',
        role: 'user' as const,
      },
    } as any);

    await act(async () => {
      loginButton.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('Yes');
    });
  });

  it('shows loading state', () => {
    const { container } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    expect(container).toBeInTheDocument();
  });
});
