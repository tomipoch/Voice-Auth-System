/**
 * Phrase Quality Rules Types
 * Types for managing phrase quality rules in the admin panel
 */

export interface PhraseRule {
  id: string;
  rule_name: string;
  rule_type: 'threshold' | 'rate_limit' | 'quality' | 'other';
  rule_value: number;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UpdateRuleRequest {
  value: number;
}

export interface UpdateRuleResponse {
  success: boolean;
  message: string;
  rule_name: string;
  new_value: number;
}

export interface ToggleRuleResponse {
  success: boolean;
  message: string;
  rule_name: string;
  is_active: boolean;
}

/**
 * Type guard to check if a value is a valid PhraseRule
 */
export const isPhraseRule = (obj: any): obj is PhraseRule => {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.rule_name === 'string' &&
    typeof obj.rule_type === 'string' &&
    typeof obj.rule_value === 'number' &&
    typeof obj.description === 'string' &&
    typeof obj.is_active === 'boolean'
  );
};
