/**
 * Phrase Rule Editor Modal
 * Modal component for editing phrase quality rule values
 */

import { useState, useEffect } from 'react';
import type { PhraseRule } from '../../types/phraseRules';
import { getRuleDetail, getCategoryColor } from '../../utils/ruleDetails';

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
        className="fixed inset-0 backdrop-blur-sm bg-white/30 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 my-8">
          {/* Header */}
          <div className="mb-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Editar Regla</h2>
            <p className="text-sm text-gray-600">
              {rule.rule_name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
            </p>
          </div>

          {/* Description */}
          <div className="mb-4 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-900">{rule.description}</p>
          </div>

          {/* Detailed Information */}
          {ruleDetail && (
            <div className="mb-4">
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center justify-between w-full text-left text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                <span>📖 Información Detallada</span>
                <span className="text-gray-400">{showDetails ? '▼' : '▶'}</span>
              </button>

              {showDetails && (
                <div className="mt-3 space-y-3 text-sm">
                  {/* Category */}
                  <div>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(ruleDetail.category)}`}
                    >
                      {ruleDetail.category}
                    </span>
                  </div>

                  {/* Impact */}
                  <div className="p-3 bg-yellow-50 rounded-md border border-yellow-200">
                    <div className="font-medium text-yellow-900 mb-1">⚠️ Impacto</div>
                    <p className="text-yellow-800">{ruleDetail.impact}</p>
                  </div>

                  {/* Recommended Range */}
                  <div className="p-3 bg-green-50 rounded-md border border-green-200">
                    <div className="font-medium text-green-900 mb-1">✅ Rango Recomendado</div>
                    <p className="text-green-800">{ruleDetail.recommendedRange}</p>
                  </div>

                  {/* Examples */}
                  <div className="p-3 bg-gray-50 rounded-md border border-gray-200">
                    <div className="font-medium text-gray-900 mb-2">💡 Ejemplos</div>
                    <ul className="space-y-1 text-gray-700">
                      {ruleDetail.examples.map((example, index) => (
                        <li key={index} className="flex items-start">
                          <span className="mr-2">•</span>
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
            <div className="text-sm text-gray-500 mb-1">Valor Actual</div>
            <div className="text-2xl font-bold text-gray-900">{rule.rule_value}</div>
          </div>

          {/* Input */}
          <div className="mb-4">
            <label htmlFor="rule-value" className="block text-sm font-medium text-gray-700 mb-2">
              Nuevo Valor
            </label>
            <input
              id="rule-value"
              type="number"
              step="any"
              value={value}
              onChange={handleChange}
              onKeyDown={handleKeyDown}
              className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                error ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Ingrese el nuevo valor"
              autoFocus
            />
            {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
          </div>

          {/* Range hint */}
          {rule.rule_type === 'threshold' && (
            <div className="mb-4 text-xs text-gray-500">
              💡 Los thresholds deben estar entre 0.0 y 1.0
            </div>
          )}
          {rule.rule_type === 'rate_limit' && (
            <div className="mb-4 text-xs text-gray-500">
              💡 Los límites de tasa deben ser números enteros positivos
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !!error || !value}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
