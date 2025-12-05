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
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  has_voiceprint: boolean;
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
   * Activar/desactivar una regla
   */
  async toggleRule(ruleName: string): Promise<ToggleRuleResponse> {
    const response = await api.post<ToggleRuleResponse>(
      `${this.baseUrl}/phrase-rules/${ruleName}/toggle`
    );
    return response.data;
  }
}

export const adminService = new AdminService();
export default adminService;
