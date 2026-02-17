/**
 * Phrase Rule Card Component
 * Displays individual phrase quality rule with edit and toggle functionality
 */

import { useState } from 'react';
import { Settings, Shield, Activity, BarChart, Hash, Clock } from 'lucide-react';
import type { PhraseRule } from '../../types/phraseRules';
import { getRuleDetail } from '../../utils/ruleDetails';

interface PhraseRuleCardProps {
  rule: PhraseRule;
  onEdit: (rule: PhraseRule) => void;
  onToggle: (ruleName: string, isActive: boolean) => void;
}

export const PhraseRuleCard = ({ rule, onEdit, onToggle }: PhraseRuleCardProps) => {
  const [isTogglingLoading, setIsToggling] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const ruleDetail = getRuleDetail(rule.rule_name);

  // Choose icon based on rule name/type
  const getRuleIcon = () => {
    if (rule.rule_name.includes('threshold') || rule.rule_name.includes('score')) return Shield;
    if (rule.rule_name.includes('rate') || rule.rule_name.includes('max')) return Activity;
    if (rule.rule_name.includes('length')) return BarChart;
    return Hash;
  };

  const RuleIcon = getRuleIcon();

  const handleToggleClick = async () => {
    setIsToggling(true);
    try {
      await onToggle(rule.rule_name, !rule.is_active);
    } finally {
      setIsToggling(false);
    }
  };

  const getFormattedValue = () => {
    const unit = ruleDetail?.unit;

    // If explicit unit is %, format as percentage
    if (unit === '%') {
      return `${(rule.rule_value * 100).toFixed(0)}%`;
    }

    // If explicit unit exists (and is not %), use it directly
    if (unit) {
      return `${rule.rule_value} ${unit}`;
    }

    // Fallback: legacy threshold check if no unit defined
    if (rule.rule_type === 'threshold') {
      return `${(rule.rule_value * 100).toFixed(0)}%`;
    }

    return rule.rule_value;
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700 flex flex-col h-full overflow-hidden group">
      {/* Header */}
      <div className="p-4 flex items-start justify-between pb-2">
        <div className="flex items-center gap-3">
          <div
            className={`p-1.5 rounded-lg ${
              rule.is_active
                ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400'
                : 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            <RuleIcon className="w-4.5 h-4.5" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 leading-tight text-sm">
              {rule.rule_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </h3>
            <span
              className={`text-[10px] uppercase tracking-wider font-bold ${
                rule.is_active ? 'text-green-600 dark:text-green-400' : 'text-gray-400'
              }`}
            >
              {rule.is_active ? 'Activa' : 'Inactiva'}
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-1 flex-1">
        {/* Current Value */}
        <div className="mb-3">
          <div className="text-[10px] font-medium text-gray-500 dark:text-gray-400 mb-0.5">
            VALOR ACTUAL
          </div>
          <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {getFormattedValue()}
          </div>
        </div>

        {/* Progress Bar for Thresholds */}
        {rule.rule_type === 'threshold' && (
          <div className="w-full h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden mb-3">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                rule.rule_value > 0.8
                  ? 'bg-green-500'
                  : rule.rule_value > 0.5
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(rule.rule_value * 100, 100)}%` }}
            />
          </div>
        )}

        {/* Description */}
        <p className="text-xs text-gray-600 dark:text-gray-300 mb-3 h-8 line-clamp-2 leading-relaxed">
          {rule.description}
        </p>

        {/* Details Toggle */}
        {ruleDetail && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium flex items-center gap-1 transition-colors"
          >
            {showDetails ? '▼' : '▶'} Ver detalles
          </button>
        )}
      </div>

      {/* Expandable Details */}
      {showDetails && ruleDetail && (
        <div className="px-4 pb-3 space-y-2 border-t border-gray-100 dark:border-gray-700 pt-3 bg-gray-50 dark:bg-gray-800/50">
          <div className="text-xs">
            <div className="font-medium text-gray-700 dark:text-gray-300 mb-0.5">Impacto</div>
            <p className="text-gray-600 dark:text-gray-400 leading-snug">{ruleDetail.impact}</p>
          </div>

          <div className="text-xs">
            <div className="font-medium text-gray-700 dark:text-gray-300 mb-0.5">
              Rango Recomendado
            </div>
            <p className="text-gray-600 dark:text-gray-400">{ruleDetail.recommendedRange}</p>
          </div>
        </div>
      )}

      {/* Footer / Actions */}
      <div className="px-4 py-2.5 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        {/* Update Date */}
        <div className="flex items-center gap-1.5 text-[10px] text-gray-500 dark:text-gray-400">
          <Clock className="w-3 h-3" />
          {new Date(rule.updated_at).toLocaleDateString('es-ES')}
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle Switch */}
          <div
            onClick={handleToggleClick}
            className={`relative inline-flex h-6 w-10 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              rule.is_active ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-600'
            } ${isTogglingLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
            style={{ width: '40px', height: '24px', borderRadius: '9999px' }}
            title={rule.is_active ? 'Desactivar regla' : 'Activar regla'}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                rule.is_active ? 'translate-x-4' : 'translate-x-0'
              }`}
              style={{ width: '20px', height: '20px' }}
            />
          </div>

          {/* Edit Button */}
          <button
            onClick={() => onEdit(rule)}
            className="flex items-center gap-1 px-2.5 py-1 text-[10px] font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors shadow-sm"
            title="Editar configuración de esta regla"
          >
            <Settings className="w-3 h-3" />
            <span>Editar</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default PhraseRuleCard;
