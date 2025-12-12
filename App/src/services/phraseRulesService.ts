/**
 * Phrase Rules Service
 * Service for managing phrase quality rules
 */

import api from './api';
import type {
  PhraseRule,
  UpdateRuleRequest,
  UpdateRuleResponse,
  ToggleRuleResponse,
} from '../types/phraseRules';

class PhraseRulesService {
  private readonly baseUrl = '/admin/phrase-rules';

  /**
   * Get all phrase quality rules
   * @param includeInactive - Include inactive rules in the response
   */
  async getRules(includeInactive = false): Promise<PhraseRule[]> {
    const response = await api.get<PhraseRule[]>(this.baseUrl, {
      params: { include_inactive: includeInactive },
    });
    return response.data;
  }

  /**
   * Update a phrase quality rule value
   * @param ruleName - Name of the rule to update
   * @param value - New value for the rule
   */
  async updateRule(ruleName: string, value: number): Promise<UpdateRuleResponse> {
    const response = await api.patch<UpdateRuleResponse>(`${this.baseUrl}/${ruleName}`, {
      value,
    } as UpdateRuleRequest);
    return response.data;
  }

  /**
   * Toggle a phrase quality rule (enable/disable)
   * @param ruleName - Name of the rule to toggle
   * @param isActive - True to enable, false to disable
   */
  async toggleRule(ruleName: string, isActive: boolean): Promise<ToggleRuleResponse> {
    const response = await api.post<ToggleRuleResponse>(
      `${this.baseUrl}/${ruleName}/toggle`,
      null,
      {
        params: { is_active: isActive },
      }
    );
    return response.data;
  }
}

export const phraseRulesService = new PhraseRulesService();
export default phraseRulesService;
