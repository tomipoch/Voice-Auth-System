import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuth } from '../useAuth';
import { AuthContext } from '../../context/AuthContext';
import { ReactNode } from 'react';

describe('useAuth', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUser = {
    id: '1',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user' as const,
  };

  const createWrapper = (contextValue: any) => {
    return ({ children }: { children: ReactNode }) => (
      <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
    );
  };

  it('returns user from context', () => {
    const mockContext = {
      user: mockUser,
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
      refreshUser: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toEqual(mockUser);
  });

  it('returns loading state', () => {
    const mockContext = {
      user: null,
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: true,
      refreshUser: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.isLoading).toBe(true);
  });

  it('returns login function', () => {
    const mockLogin = vi.fn();
    const mockContext = {
      user: null,
      login: mockLogin,
      logout: vi.fn(),
      isLoading: false,
      refreshUser: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.login).toBe(mockLogin);
  });

  it('returns logout function', () => {
    const mockLogout = vi.fn();
    const mockContext = {
      user: mockUser,
      login: vi.fn(),
      logout: mockLogout,
      isLoading: false,
      refreshUser: vi.fn(),
    };

    const wrapper = createWrapper(mockContext);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.logout).toBe(mockLogout);
  });

  it('returns refreshUser function', () => {
    const mockRefreshUser = vi.fn();
    const mockContext = {
      user: mockUser,
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
      refreshUser: mockRefreshUser,
    };

    const wrapper = createWrapper(mockContext);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.refreshUser).toBe(mockRefreshUser);
  });

  it('throws error when used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      renderHook(() => useAuth());
    }).toThrow('useAuth debe ser usado dentro de un AuthProvider');

    consoleErrorSpy.mockRestore();
  });
});
