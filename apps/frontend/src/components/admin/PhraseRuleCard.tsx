/**
 * Phrase Rule Card Component
 * Displays individual phrase quality rule with edit and toggle functionality
 */

import { useState } from 'react';
import { Settings, Shield, Activity, BarChart, Hash } from 'lucide-react';
import type { PhraseRule } from '../../types/phraseRules';
import { getRuleDetail } from '../../utils/ruleDetails';

interface PhraseRuleCardProps {
  rule: PhraseRule;
  onEdit: (rule: PhraseRule) => void;
  onToggle: (ruleName: string, isActive: boolean) => void;
}

export const PhraseRuleCard = ({ rule, onEdit, onToggle }: PhraseRuleCardProps) => {
  const [isToggling, setIsToggling] = useState(false);
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
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 flex flex-col h-full overflow-hidden shadow-sm transition-shadow hover:shadow-md">
      {/* Header */}
      <div className="p-4 flex items-start justify-between pb-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-50 dark:bg-gray-700/50 rounded-xl flex items-center justify-center">
            <RuleIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-800 dark:text-gray-100 leading-tight">
              {rule.rule_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`w-1.5 h-1.5 rounded-full ${rule.is_active ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`} />
              <span className="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wider">
                {rule.is_active ? 'Activa' : 'Inactiva'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-4 py-1 flex-1">
        {/* Integrated Value & Description Display */}
        <div className="bg-gray-50 dark:bg-gray-900/40 rounded-xl p-4 border border-gray-100 dark:border-gray-800/30 mb-3">
          <div className="flex justify-between items-baseline mb-1">
            <div>
              <div className="text-[9px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-0.5">
                VALOR ACTUAL
              </div>
              <div className="text-2xl font-bold text-gray-950 dark:text-white tabular-nums">
                {getFormattedValue()}
              </div>
            </div>
            {rule.rule_type === 'threshold' && (
              <div className="text-right">
                <div className="text-[9px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest mb-0.5">
                  EXIGENCIA
                </div>
                <div className="text-xs font-bold text-blue-600 dark:text-blue-400">
                  {(rule.rule_value * 100).toFixed(0)}%
                </div>
              </div>
            )}
          </div>

          <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed line-clamp-2 mb-1">
            {rule.description}
          </p>

          {/* Integrated Impact Details */}
          {ruleDetail && (
            <div className="pt-1.5 border-t border-gray-200/40 dark:border-gray-700/40">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-[10px] text-blue-600 dark:text-blue-400 font-bold flex items-center gap-1.5 hover:underline"
              >
                {showDetails ? '↑ Ocultar detalles' : '↓ Ver impacto'}
              </button>

              {showDetails && (
                <div className="mt-2 space-y-2 animate-in fade-in slide-in-from-top-1 duration-200">
                  <div className="text-[10px] leading-snug">
                    <span className="font-bold text-gray-600 dark:text-gray-400 uppercase">Impacto: </span>
                    <span className="text-gray-500 dark:text-gray-500 italic">"{ruleDetail.impact}"</span>
                  </div>
                  <div className="text-[10px]">
                    <span className="font-bold text-gray-600 dark:text-gray-400 uppercase">Recomendado: </span>
                    <span className="text-gray-900 dark:text-gray-200 font-bold">{ruleDetail.recommendedRange}</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Progress Bar for Thresholds */}
        {rule.rule_type === 'threshold' && (
          <div className="px-1 mb-3">
            <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-700 ${
                  rule.rule_value > 0.8
                    ? 'bg-green-500'
                    : rule.rule_value > 0.5
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(rule.rule_value * 100, 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Footer / Actions */}
      <div className="px-4 py-2.5 bg-gray-50/50 dark:bg-gray-900/60 border-t border-gray-100 dark:border-gray-800/80 flex items-center justify-between mt-auto">
        <div className="text-[9px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-widest">
          {new Date(rule.updated_at).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
        </div>

        <div className="flex items-center gap-3">
          {/* Toggle Switch - Preserved */}
          <div
            onClick={handleToggleClick}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              rule.is_active ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-600'
            } ${isToggling ? 'opacity-50 cursor-not-allowed' : ''}`}
            style={{ width: '36px', height: '20px', borderRadius: '9999px' }}
            title={rule.is_active ? 'Desactivar regla' : 'Activar regla'}
          >
            <span
              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                rule.is_active ? 'translate-x-4' : 'translate-x-0'
              }`}
              style={{ width: '16px', height: '16px' }}
            />
          </div>

          <button
            onClick={() => onEdit(rule)}
            className="flex items-center gap-1 px-2 py-1 text-[10px] font-bold text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Settings className="w-3 h-3" />
            Editar
          </button>
        </div>
      </div>
    </div>
  );
};

export default PhraseRuleCard;
