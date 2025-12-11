/**
 * Phrase Rule Card Component
 * Displays individual phrase quality rule with edit and toggle functionality
 */

import { useState } from 'react';
import type { PhraseRule } from '../../types/phraseRules';
import { getRuleDetail, getCategoryColor } from '../../utils/ruleDetails';

interface PhraseRuleCardProps {
  rule: PhraseRule;
  onEdit: (rule: PhraseRule) => void;
  onToggle: (ruleName: string, isActive: boolean) => void;
}

export const PhraseRuleCard = ({ rule, onEdit, onToggle }: PhraseRuleCardProps) => {
  const [isTogglingLoading, setIsToggling] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const ruleDetail = getRuleDetail(rule.rule_name);

  const handleToggle = async () => {
    setIsToggling(true);
    try {
      await onToggle(rule.rule_name, !rule.is_active);
    } finally {
      setIsToggling(false);
    }
  };

  const getRuleTypeColor = (type: string) => {
    switch (type) {
      case 'threshold':
        return 'bg-blue-100 text-blue-800';
      case 'rate_limit':
        return 'bg-yellow-100 text-yellow-800';
      case 'cleanup':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Format value with unit
  const getFormattedValue = () => {
    const value = rule.rule_value;
    const ruleName = rule.rule_name;

    // Threshold rules (percentages)
    if (rule.rule_type === 'threshold' && value <= 1) {
      return `${(value * 100).toFixed(0)}%`;
    }

    // Specific rules with units
    if (ruleName === 'challenge_expiry_minutes') {
      return `${value} ${value === 1 ? 'minuto' : 'minutos'}`;
    }
    if (ruleName === 'cleanup_expired_after_hours' || ruleName === 'cleanup_used_after_hours') {
      return `${value} ${value === 1 ? 'hora' : 'horas'}`;
    }
    if (ruleName === 'min_attempts_for_analysis') {
      return `${value} ${value === 1 ? 'intento' : 'intentos'}`;
    }
    if (ruleName === 'exclude_recent_phrases') {
      return `${value} ${value === 1 ? 'frase' : 'frases'}`;
    }
    if (ruleName === 'max_challenges_per_user' || ruleName === 'max_challenges_per_hour') {
      return `${value} ${value === 1 ? 'challenge' : 'challenges'}`;
    }

    // Default: just the number
    return value.toString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-all">
      {/* Header */}
      <div className="p-6 pb-4">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              {rule.rule_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRuleTypeColor(rule.rule_type)}`}
              >
                {rule.rule_type}
              </span>
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  rule.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}
              >
                {rule.is_active ? 'Activa' : 'Inactiva'}
              </span>
              {ruleDetail && (
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(ruleDetail.category)}`}
                >
                  {ruleDetail.category}
                </span>
              )}
            </div>
          </div>

          {/* Toggle Switch */}
          <label className="relative inline-flex items-center cursor-pointer ml-2">
            <input
              type="checkbox"
              checked={rule.is_active}
              onChange={handleToggle}
              disabled={isTogglingLoading}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
          </label>
        </div>

        {/* Current Value */}
        <div className="mb-4">
          <div className="text-sm text-gray-500 mb-1">Valor Actual</div>
          <div className="text-3xl font-bold text-gray-900">{getFormattedValue()}</div>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-3">{rule.description}</p>

        {/* Details Toggle */}
        {ruleDetail && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1"
          >
            {showDetails ? '▼' : '▶'} Ver detalles
          </button>
        )}
      </div>

      {/* Expandable Details */}
      {showDetails && ruleDetail && (
        <div className="px-6 pb-4 space-y-3 border-t border-gray-100 pt-4">
          {/* Impact */}
          <div className="text-sm">
            <div className="font-medium text-gray-700 mb-1">⚠️ Impacto</div>
            <p className="text-gray-600">{ruleDetail.impact}</p>
          </div>

          {/* Recommended Range */}
          <div className="text-sm">
            <div className="font-medium text-gray-700 mb-1">✅ Rango Recomendado</div>
            <p className="text-gray-600">{ruleDetail.recommendedRange}</p>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="px-6 pb-6 flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="text-xs text-gray-400">
          Actualizada: {new Date(rule.updated_at).toLocaleDateString('es-ES')}
        </div>
        <button
          onClick={() => onEdit(rule)}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          ✏️ Editar
        </button>
      </div>
    </div>
  );
};

export default PhraseRuleCard;

