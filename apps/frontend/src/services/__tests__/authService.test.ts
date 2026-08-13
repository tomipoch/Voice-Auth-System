/**
 * Unit tests for the typed AuthService in services/authService.ts.
 *
 * Covers the public contract used by AuthContext, ProfilePage and
 * SettingsPage: login/refresh persist tokens via authStorage; logout
 * is fully client-side; profile updates and password changes return
 * the real backend shape ({success, message}) and let axios throw
 * on HTTP errors.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { authService } from '../authService';
import { authStorage } from '../storage';

const mockedPost = vi.mocked(api.post);
const mockedGet = vi.mocked(api.get);
const mockedPatch = vi.mocked(api.patch);

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    authStorage.clearAuth();
  });

  describe('login', () => {
    it('posts credentials to /auth/login and persists tokens', async () => {
      const backendResponse = {
        access_token: 'access-abc',
        token_type: 'bearer' as const,
        expires_in: 7200,
        refresh_token: 'refresh-xyz',
        user: {
          id: '11111111-1111-1111-1111-111111111111',
          email: 'u@example.com',
          name: 'Test User',
          first_name: 'Test',
          last_name: 'User',
          role: 'user' as const,
          created_at: '2024-01-01T00:00:00Z',
        },
      };
      mockedPost.mockResolvedValueOnce({ data: backendResponse });

      const result = await authService.login({
        email: 'u@example.com',
        password: 'Password1!',
      });

      expect(mockedPost).toHaveBeenCalledWith('/auth/login', {
        email: 'u@example.com',
        password: 'Password1!',
      });
      expect(result).toEqual(backendResponse);
      expect(authStorage.getAccessToken()).toBe('access-abc');
      expect(authStorage.getRefreshToken()).toBe('refresh-xyz');
      expect(authStorage.getUser()?.id).toBe(backendResponse.user.id);
    });

    it('lets axios errors propagate', async () => {
      mockedPost.mockRejectedValueOnce(new Error('Invalid credentials'));
      await expect(
        authService.login({ email: 'u@example.com', password: 'wrong' }),
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('register', () => {
    it('posts RegisterData and returns {success, user_id, email}', async () => {
      mockedPost.mockResolvedValueOnce({
        data: { success: true, user_id: 'u-2', email: 'new@example.com' },
      });

      const payload = {
        email: 'new@example.com',
        password: 'Password1!',
        first_name: 'New',
        last_name: 'User',
        rut: '12345678-9',
      };
      const result = await authService.register(payload);

      expect(mockedPost).toHaveBeenCalledWith('/auth/register', payload);
      expect(result).toEqual({ success: true, user_id: 'u-2', email: 'new@example.com' });
      expect(authStorage.getAccessToken()).toBeNull();
    });
  });

  describe('logout', () => {
    it('clears auth storage and never calls the API', async () => {
      authStorage.setAccessToken('a');
      authStorage.setRefreshToken('r');
      authStorage.setUser({
        id: '1',
        email: 'x@y.com',
        name: 'X',
        role: 'user',
        created_at: '2024-01-01T00:00:00Z',
      });

      await authService.logout();

      expect(mockedPost).not.toHaveBeenCalled();
      expect(authStorage.getAccessToken()).toBeNull();
    });
  });

  describe('getProfile', () => {
    it('GETs /auth/me and persists the user', async () => {
      const profile = {
        id: '1',
        email: 'p@example.com',
        name: 'Profile User',
        first_name: 'Profile',
        last_name: 'User',
        role: 'admin' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockedGet.mockResolvedValueOnce({ data: profile });

      const result = await authService.getProfile();

      expect(mockedGet).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(profile);
      expect(authStorage.getUser()).toEqual(profile);
    });
  });

  describe('refreshToken', () => {
    it('posts to /auth/refresh and stores the new access token', async () => {
      authStorage.setRefreshToken('old-refresh');
      mockedPost.mockResolvedValueOnce({
        data: {
          access_token: 'new-access',
          token_type: 'bearer' as const,
          expires_in: 7200,
          user: {
            id: '1',
            email: 'r@example.com',
            name: 'R',
            role: 'user' as const,
            created_at: '2024-01-01T00:00:00Z',
          },
        },
      });

      const result = await authService.refreshToken();

      expect(mockedPost).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: 'old-refresh',
      });
      expect(result.access_token).toBe('new-access');
      expect(authStorage.getAccessToken()).toBe('new-access');
    });

    it('throws when no refresh token is stored', async () => {
      await expect(authService.refreshToken()).rejects.toThrow(
        'No refresh token available',
      );
      expect(mockedPost).not.toHaveBeenCalled();
    });
  });

  describe('updateProfile', () => {
    it('PATCHes /auth/profile and returns the backend envelope', async () => {
      mockedPatch.mockResolvedValueOnce({
        data: { success: true, message: 'Profile updated' },
      });

      const result = await authService.updateProfile({
        first_name: 'Nuevo',
        last_name: 'Apellido',
      });

      expect(mockedPatch).toHaveBeenCalledWith('/auth/profile', {
        first_name: 'Nuevo',
        last_name: 'Apellido',
      });
      expect(result).toEqual({ success: true, message: 'Profile updated' });
    });
  });

  describe('changePassword', () => {
    it('POSTs current/new passwords to /auth/change-password', async () => {
      mockedPost.mockResolvedValueOnce({
        data: { success: true, message: 'Password changed' },
      });

      const result = await authService.changePassword('Old123!', 'New456!');

      expect(mockedPost).toHaveBeenCalledWith('/auth/change-password', {
        current_password: 'Old123!',
        new_password: 'New456!',
      });
      expect(result).toEqual({ success: true, message: 'Password changed' });
    });

    it('lets axios errors propagate on bad credentials', async () => {
      mockedPost.mockRejectedValueOnce({
        response: { data: { detail: 'Current password is incorrect' } },
      });
      await expect(authService.changePassword('wrong', 'New456!')).rejects.toBeDefined();
    });
  });
});
