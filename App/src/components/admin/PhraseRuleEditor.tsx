/**
 * Phrase Rule Editor Modal
 * Modal component for editing phrase quality rule values
 */

import { useState, useEffect } from 'react';
import type { PhraseRule } from '../../types/phraseRules';
import { getRuleDetail } from '../../utils/ruleDetails';

interface PhraseRuleEditorProps {
  rule: PhraseRule | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (ruleName: string, newValue: number) => Promise<void>;
}

export const PhraseRuleEditor = ({ rule, isOpen, onClose, onSave }: PhraseRuleEditorProps) => {
  const [value, setValue] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [showDetails, setShowDetails] = useState(true);

  useEffect(() => {
    if (rule) {
      setValue(rule.rule_value.toString());
      setError('');
    }
  }, [rule]);

  if (!isOpen || !rule) return null;

  const ruleDetail = getRuleDetail(rule.rule_name);

  const validateValue = (val: string): boolean => {
    const numValue = parseFloat(val);
    if (isNaN(numValue)) {
      setError('Debe ingresar un número válido');
      return false;
    }

    if (numValue < 0) {
      setError('El valor no puede ser negativo');
      return false;
    }

    // Rule-specific validations
    if (rule.rule_type === 'threshold' && (numValue < 0 || numValue > 1)) {
      setError('Los thresholds deben estar entre 0 y 1');
      return false;
    }

    if (rule.rule_type === 'rate_limit' && numValue < 1) {
      setError('Los límites de tasa deben ser al menos 1');
      return false;
    }

    setError('');
    return true;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);
    if (newValue) {
      validateValue(newValue);
    } else {
      setError('');
    }
  };

  const handleSave = async () => {
    if (!validateValue(value)) {
      return;
    }

    setIsSaving(true);
    try {
      await onSave(rule.rule_name, parseFloat(value));
      onClose();
    } catch {
      setError('Error al guardar. Intente nuevamente.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !error && value) {
      handleSave();
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <>
      {/* Backdrop with blur */}
      <div
        className="fixed inset-0 backdrop-blur-sm bg-black/30 dark:bg-black/60 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full p-6 my-8 border border-gray-200 dark:border-gray-700">
          {/* Header */}
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Editar Regla</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {rule.rule_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </p>
          </div>

          {/* Description */}
          <div className="mb-4 text-sm text-gray-600 dark:text-gray-300">
            {rule.description}
          </div>

          {/* Detailed Information */}
          {ruleDetail && (
            <div className="mb-6 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center justify-between w-full px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <span>Detalles de configuración</span>
                <span className="text-gray-500 dark:text-gray-400">{showDetails ? '▼' : '▶'}</span>
              </button>

              {showDetails && (
                <div className="p-4 space-y-4 bg-white dark:bg-gray-900/30">
                  {/* Category */}
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Categoría</span>
                    <div className="mt-1">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border border-gray-200 dark:border-gray-700 uppercase">
                        {ruleDetail.category}
                      </span>
                    </div>
                  </div>

                  {/* Impact */}
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Impacto</span>
                    <p className="mt-1 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{ruleDetail.impact}</p>
                  </div>

                  {/* Recommended Range */}
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Rango Recomendado</span>
                    <p className="mt-1 text-sm text-gray-700 dark:text-gray-300 font-medium">{ruleDetail.recommendedRange}</p>
                  </div>

                  {/* Examples */}
                  <div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider font-semibold">Ejemplos</span>
                    <ul className="mt-1 space-y-1 text-sm text-gray-600 dark:text-gray-400">
                      {ruleDetail.examples.map((example, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2 text-gray-400">•</span>
                          <span>{example}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Current Value */}
          <div className="mb-4">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Valor Actual</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{rule.rule_value}</div>
          </div>

          {/* Input */}
          <div className="mb-4">
            <label htmlFor="rule-value" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Nuevo Valor
            </label>
            <input
              id="rule-value"
              type="number"
              step="any"
              value={value}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 ${
                error ? 'border-red-300 dark:border-red-700' : 'border-gray-300 dark:border-gray-600'
              }`}
              placeholder="Ingrese el nuevo valor"
              autoFocus
            />
            {error && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>}
          </div>

          {/* Range hint */}
          {rule.rule_type === 'threshold' && (
            <div className="mb-4 text-xs text-gray-500 dark:text-gray-400">
              💡 Los thresholds deben estar entre 0.0 y 1.0
            </div>
          )}
          {rule.rule_type === 'rate_limit' && (
            <div className="mb-4 text-xs text-gray-500 dark:text-gray-400">
              💡 Los límites de tasa deben ser números enteros positivos
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !!error || !value}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSaving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default PhraseRuleEditor;
