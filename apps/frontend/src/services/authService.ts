/**
 * AuthService - typed wrapper over the FastAPI auth endpoints.
 *
 * Replaces the untyped mock-routed facade at apiServices.ts. Each method
 * matches the actual Pydantic response shape from
 * apps/backend/src/api/auth_controller.py (TokenResponse,
 * UserProfile, etc.) so consumers can rely on the real contract.
 *
 * Side-effects:
 * - login() and refreshToken() persist access_token via authStorage.
 * - logout() clears the local auth state (backend has no logout endpoint
 *   - JWT is stateless).
 */

import api from './api';
import { authStorage } from './storage';
import type { AuthResponse, LoginCredentials, RegisterData, User } from '../types';

export interface RegisterResponse {
  success: boolean;
  user_id: string;
  email: string;
}

export interface ProfileUpdateResponse {
  success: boolean;
  message: string;
}

export interface ChangePasswordResponse {
  success: boolean;
  message: string;
}

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/login', credentials);
    if (data.access_token) {
      authStorage.setAccessToken(data.access_token);
    }
    if (data.refresh_token) {
      authStorage.setRefreshToken(data.refresh_token);
    }
    if (data.user) {
      authStorage.setUser(data.user);
    }
    return data;
  }

  async register(userData: RegisterData): Promise<RegisterResponse> {
    const { data } = await api.post<RegisterResponse>('/auth/register', userData);
    return data;
  }

  async logout(): Promise<void> {
    authStorage.clearAuth();
  }

  async getProfile(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    authStorage.setUser(data);
    return data;
  }

  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = authStorage.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const { data } = await api.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    if (data.access_token) {
      authStorage.setAccessToken(data.access_token);
    }
    return data;
  }

  async updateProfile(payload: Partial<User>): Promise<ProfileUpdateResponse> {
    const { data } = await api.patch<ProfileUpdateResponse>('/auth/profile', payload);
    return data;
  }

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<ChangePasswordResponse> {
    const { data } = await api.post<ChangePasswordResponse>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return data;
  }
}

export const authService = new AuthService();
export default authService;
