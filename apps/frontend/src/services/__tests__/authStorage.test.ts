import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authStorage } from '../storage';

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

describe('authStorage', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Access Token', () => {
    it('sets and gets access token', () => {
      authStorage.setAccessToken('test-token');
      expect(authStorage.getAccessToken()).toBe('test-token');
    });

    it('returns null when no access token exists', () => {
      expect(authStorage.getAccessToken()).toBeNull();
    });
  });

  describe('Refresh Token', () => {
    it('sets and gets refresh token', () => {
      authStorage.setRefreshToken('refresh-token');
      expect(authStorage.getRefreshToken()).toBe('refresh-token');
    });

    it('returns null when no refresh token exists', () => {
      expect(authStorage.getRefreshToken()).toBeNull();
    });
  });

  describe('User', () => {
    it('sets and gets user object', () => {
      const user = {
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
      };

      authStorage.setUser(user);
      const retrieved = authStorage.getUser();

      expect(retrieved).toEqual(user);
    });

    it('returns null when no user exists', () => {
      expect(authStorage.getUser()).toBeNull();
    });
  });

  describe('Is Authenticated', () => {
    it('returns true when both token and user exist', () => {
      authStorage.setAccessToken('token');
      authStorage.setUser({
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
      });

      expect(authStorage.isAuthenticated()).toBe(true);
    });

    it('returns false when only token exists', () => {
      authStorage.setAccessToken('token');
      expect(authStorage.isAuthenticated()).toBe(false);
    });

    it('returns false when only user exists', () => {
      authStorage.setUser({
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
      });
      expect(authStorage.isAuthenticated()).toBe(false);
    });

    it('returns false when neither exists', () => {
      expect(authStorage.isAuthenticated()).toBe(false);
    });
  });

  describe('Clear Auth', () => {
    it('clears all auth-related data', () => {
      authStorage.setAccessToken('token');
      authStorage.setRefreshToken('refresh');
      authStorage.setUser({
        id: '1',
        email: 'test@example.com',
        name: 'Test User',
        role: 'user' as const,
      });

      authStorage.clearAuth();

      expect(authStorage.getAccessToken()).toBeNull();
      expect(authStorage.getRefreshToken()).toBeNull();
      expect(authStorage.getUser()).toBeNull();
    });
  });
});
