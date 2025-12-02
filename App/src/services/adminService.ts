/**
 * Admin Service - Phrase Quality Rules Management
 * Servicio para gestionar las reglas de calidad de frases
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

class AdminService {
  private readonly baseUrl = '/admin';

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
