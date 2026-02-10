import { describe, it, expect, vi, beforeEach } from 'vitest';
import { authService } from '../apiServices';
import api from '../api';

// Mock the api module
vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('login', () => {
    it('successfully logs in with valid credentials', async () => {
      const mockResponse = {
        data: {
          access_token: 'test-token',
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
            role: 'user',
          },
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await authService.login({
        email: 'test@example.com',
        password: 'password123',
      });

      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });
      expect(result).toEqual(mockResponse.data);
    });

    it('handles login failure', async () => {
      const mockError = new Error('Invalid credentials');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(
        authService.login({
          email: 'test@example.com',
          password: 'wrong',
        })
      ).rejects.toThrow('Invalid credentials');
    });
  });

  describe('register', () => {
    it('successfully registers a new user', async () => {
      const mockResponse = {
        data: {
          access_token: 'new-token',
          user: {
            id: '2',
            email: 'new@example.com',
            name: 'New User',
            role: 'user',
          },
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await authService.register({
        email: 'new@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
      });

      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'new@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('logout', () => {
    it('successfully logs out and clears storage', async () => {
      localStorage.setItem('token', 'test-token');
      localStorage.setItem('user', JSON.stringify({ id: '1' }));

      const mockResponse = {
        data: {
          success: true,
          data: { message: 'Logged out' },
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await authService.logout();

      expect(api.post).toHaveBeenCalledWith('/auth/logout');
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('user')).toBeNull();
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getProfile', () => {
    it('successfully retrieves user profile', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
          },
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await authService.getProfile();

      expect(api.get).toHaveBeenCalledWith('/auth/profile');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('updateProfile', () => {
    it('successfully updates user profile', async () => {
      const mockResponse = {
        data: {
          id: '1',
          first_name: 'Updated',
          last_name: 'Name',
        },
      };

      vi.mocked(api.patch).mockResolvedValue(mockResponse);

      const result = await authService.updateProfile({
        first_name: 'Updated',
        last_name: 'Name',
      });

      expect(api.patch).toHaveBeenCalledWith('/auth/profile', {
        first_name: 'Updated',
        last_name: 'Name',
      });
      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockResponse.data);
    });
  });

  describe('changePassword', () => {
    it('successfully changes password', async () => {
      const mockResponse = {
        data: {
          success: true,
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await authService.changePassword('oldPass', 'newPass');

      expect(api.post).toHaveBeenCalledWith('/auth/change-password', {
        current_password: 'oldPass',
        new_password: 'newPass',
      });
      expect(result.success).toBe(true);
    });

    it('handles password change failure', async () => {
      const mockResponse = {
        data: {
          success: false,
          message: 'Current password is incorrect',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await authService.changePassword('wrong', 'newPass');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Current password is incorrect');
    });
  });
});
