/**
 * Admin Service - Admin Management
 * Servicio para gestionar funcionalidades administrativas
 */

import api from './api';
import type { PhraseQualityRule } from '../types';

export interface UpdateRuleRequest {
  new_value: number;
}

export interface UpdateRuleResponse {
  success: boolean;
  rule: PhraseQualityRule;
  message: string;
}

export interface ToggleRuleResponse {
  success: boolean;
  rule: PhraseQualityRule;
  message: string;
}

export interface AdminUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  is_active: boolean; // Computed from status='active' in frontend or backend? Backend returns "status": "active" string.
  // Wait, backend returns "status": "active" | "inactive".
  // AdminUser interface had is_active: boolean.
  // I should check if I need to map "status" string to is_active boolean or update interface.
  // Backend returns: status: str, enrollment_status: str.
  status: string;
  enrollment_status: string;
  created_at: string;
  // has_voiceprint: boolean; // Removed
}

export interface PaginatedUsers {
  users: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SystemStats {
  total_users: number;
  total_enrollments: number;
  total_verifications: number;
  success_rate: number;
  active_users_24h: number;
  failed_verifications_24h: number;
  daily_verifications: { date: string; count: number }[];
}

export interface AuditLog {
  id: string;
  user_id: string;
  user_name: string;
  action: string;
  timestamp: string;
  details: string;
}

export interface VoiceTemplate {
  id?: string;
  model_type?: string;
  sample_count?: number;
  created_at?: string;
}

export interface UserDetails {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  company: string;
  status: string;
  enrollment_status: string;
  created_at: string;
  last_login?: string;
  voice_template?: VoiceTemplate | null;
}

export interface VerificationAttempt {
  id: string;
  date: string;
  result: 'success' | 'failed';
  score: number;
  method: string;
  details?: Record<string, unknown>; // Contains raw metadata from backend
}

export interface UserHistoryResponse {
  success: boolean;
  history: {
    user_id: string;
    total_attempts: number;
    recent_attempts: VerificationAttempt[];
  };
}

class AdminService {
  private readonly baseUrl = '/admin';

  /**
   * Obtener estadísticas del sistema
   */
  async getStats(): Promise<SystemStats> {
    const response = await api.get<SystemStats>(`${this.baseUrl}/stats`);
    return response.data;
  }

  /**
   * Obtener lista de usuarios
   */
  async getUsers(page: number = 1, pageSize: number = 50): Promise<PaginatedUsers> {
    const response = await api.get<PaginatedUsers>(`${this.baseUrl}/users`, {
      params: { page, page_size: pageSize },
    });
    return response.data;
  }

  /**
   * Obtener detalles de un usuario
   */
  async getUserDetails(id: string): Promise<UserDetails> {
    const response = await api.get<UserDetails>(`${this.baseUrl}/users/${id}`);
    return response.data;
  }

  /**
   * Obtener historial de verificaciones de un usuario
   */
  async getUserHistory(id: string): Promise<UserHistoryResponse> {
    // Note: This calls the verification service, not admin service directly
    // but we wrap it here for convenience in the admin context
    const response = await api.get<UserHistoryResponse>(`/verification/user/${id}/history`);
    return response.data;
  }

  /**
   * Obtener todas las reglas de calidad de frases
   */
  async getPhraseRules(): Promise<PhraseQualityRule[]> {
    const response = await api.get<PhraseQualityRule[]>(`${this.baseUrl}/phrase-rules`);
    return response.data;
  }

  /**
   * Actualizar el valor de una regla
   */
  async updateRule(ruleName: string, newValue: number): Promise<UpdateRuleResponse> {
    const response = await api.patch<UpdateRuleResponse>(
      `${this.baseUrl}/phrase-rules/${ruleName}`,
      { new_value: newValue }
    );
    return response.data;
  }

  /**
   * Obtener logs de auditoría
   */
  async getLogs(limit: number = 100, action?: string): Promise<AuditLog[]> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (action) {
      params.append('action', action);
    }

    const response = await api.get<AuditLog[]>(`${this.baseUrl}/activity?${params}`);
    return response.data;
  }

  /**
   * Eliminar un usuario
   */
  async deleteUser(userId: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`${this.baseUrl}/users/${userId}`);
    return response.data;
  }

  /**
   * Actualizar información de un usuario
   */
  async updateUser(userId: string, userData: Partial<AdminUser>): Promise<{ message: string }> {
    const response = await api.patch<{ message: string }>(
      `${this.baseUrl}/users/${userId}`,
      userData
    );
    return response.data;
  }

  /**
   * Activar/desactivar una regla
   */
  async toggleRule(ruleName: string): Promise<ToggleRuleResponse> {
    const response = await api.post<ToggleRuleResponse>(
      `${this.baseUrl}/phrase-rules/${ruleName}/toggle`
    );
    return response.data;
  }

  // =====================================================
  // Notifications
  // =====================================================

  /**
   * Get notifications/alerts for admin
   */
  async getNotifications(limit: number = 20): Promise<AlertNotification[]> {
    const response = await api.get<AlertNotification[]>(
      `${this.baseUrl}/notifications?limit=${limit}`
    );
    return response.data;
  }

  // =====================================================
  // Voiceprint Management
  // =====================================================

  /**
   * Reset user's voiceprint
   */
  async resetVoiceprint(userId: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`${this.baseUrl}/users/${userId}/reset-voiceprint`);
    return response.data;
  }

  // =====================================================
  // Chart Data
  // =====================================================

  /**
   * Get chart data for verifications
   */
  async getChartData(days: number = 30): Promise<ChartDataPoint[]> {
    const response = await api.get<ChartDataPoint[]>(
      `${this.baseUrl}/stats/chart-data?days=${days}`
    );
    return response.data;
  }

  // =====================================================
  // Export
  // =====================================================

  /**
   * Export users as CSV (triggers download)
   */
  async exportUsers(): Promise<void> {
    const response = await api.get(`${this.baseUrl}/export/users`, {
      responseType: 'blob',
    });
    this.downloadBlob(response.data, `usuarios_${new Date().toISOString().split('T')[0]}.csv`);
  }

  /**
   * Export activity logs as CSV (triggers download)
   */
  async exportActivity(days: number = 30): Promise<void> {
    const response = await api.get(`${this.baseUrl}/export/activity?days=${days}`, {
      responseType: 'blob',
    });
    this.downloadBlob(response.data, `actividad_${new Date().toISOString().split('T')[0]}.csv`);
  }

  /**
   * Helper to trigger file download
   */
  private downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }
}

// New interfaces
export interface AlertNotification {
  id: string;
  type: 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: string;
  user_id?: string;
  user_email?: string;
  is_read: boolean;
}

export interface ChartDataPoint {
  date: string;
  verifications: number;
  successful: number;
  failed: number;
}

export const adminService = new AdminService();
export default adminService;
