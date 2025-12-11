/**
 * PhraseRulesPage - Admin UI for Phrase Quality Rules
 * Interfaz de administración para configurar reglas de calidad de frases
 */

import { useState, useEffect } from 'react';
import { Settings, Save, RotateCcw, AlertCircle, CheckCircle2 } from 'lucide-react';
import adminService from '../../services/adminService';
import type { PhraseQualityRule } from '../../types';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

interface RuleConfig {
  min: number;
  max: number;
  step: number;
  unit: string;
  description: string;
}

const RULE_CONFIGS: Record<string, RuleConfig> = {
  min_success_rate: {
    min: 0.5,
    max: 1.0,
    step: 0.05,
    unit: '%',
    description: 'Tasa mínima de éxito para mantener una frase activa',
  },
  min_asr_score: {
    min: 0.5,
    max: 1.0,
    step: 0.05,
    unit: '%',
    description: 'Score mínimo de reconocimiento de voz (ASR)',
  },
  min_phrase_ok_rate: {
    min: 0.5,
    max: 1.0,
    step: 0.05,
    unit: '%',
    description: 'Tasa mínima de transcripción correcta',
  },
  min_attempts_for_analysis: {
    min: 5,
    max: 50,
    step: 5,
    unit: 'intentos',
    description: 'Intentos mínimos antes de analizar performance',
  },
  exclude_recent_phrases: {
    min: 10,
    max: 100,
    step: 10,
    unit: 'frases',
    description: 'Número de frases recientes a excluir',
  },
  max_challenges_per_user: {
    min: 1,
    max: 10,
    step: 1,
    unit: 'challenges',
    description: 'Máximo de challenges activos por usuario',
  },
  max_challenges_per_hour: {
    min: 5,
    max: 100,
    step: 5,
    unit: 'challenges',
    description: 'Máximo de challenges por hora por usuario',
  },
  challenge_expiry_minutes: {
    min: 1,
    max: 60,
    step: 1,
    unit: 'minutos',
    description: 'Tiempo de expiración de challenges',
  },
  cleanup_expired_after_hours: {
    min: 1,
    max: 24,
    step: 1,
    unit: 'horas',
    description: 'Borrar challenges expirados después de N horas',
  },
  cleanup_used_after_hours: {
    min: 1,
    max: 168,
    step: 1,
    unit: 'horas',
    description: 'Borrar challenges usados después de N horas',
  },
};

const RULE_CATEGORIES = {
  threshold: {
    title: '📊 Thresholds',
    description: 'Umbrales de calidad para frases',
    rules: ['min_success_rate', 'min_asr_score', 'min_phrase_ok_rate', 'min_attempts_for_analysis'],
  },
  rate_limit: {
    title: '⏱️ Rate Limits',
    description: 'Límites de uso de challenges',
    rules: ['exclude_recent_phrases', 'max_challenges_per_user', 'max_challenges_per_hour'],
  },
  cleanup: {
    title: '🧹 Cleanup',
    description: 'Configuración de limpieza automática',
    rules: ['challenge_expiry_minutes', 'cleanup_expired_after_hours', 'cleanup_used_after_hours'],
  },
};

const PhraseRulesPage = () => {
  const [rules, setRules] = useState<PhraseQualityRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [pendingChanges, setPendingChanges] = useState<Record<string, number>>({});

  // Load rules on mount
  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getPhraseRules();
      setRules(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar reglas');
    } finally {
      setLoading(false);
    }
  };

  const handleSliderChange = (ruleName: string, value: number) => {
    setPendingChanges((prev) => ({
      ...prev,
      [ruleName]: value,
    }));
  };

  const handleSaveRule = async (ruleName: string) => {
    const newValue = pendingChanges[ruleName];
    if (newValue === undefined) return;

    try {
      setSaving(ruleName);
      setError(null);
      setSuccessMessage(null);

      await adminService.updateRule(ruleName, newValue);

      // Update local state
      setRules((prev) =>
        prev.map((rule) =>
          rule.rule_name === ruleName ? { ...rule, rule_value: newValue } : rule
        )
      );

      // Remove from pending changes
      setPendingChanges((prev) => {
        const { [ruleName]: _, ...rest } = prev;
        return rest;
      });

      setSuccessMessage(`Regla "${ruleName}" actualizada correctamente`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al actualizar regla');
    } finally {
      setSaving(null);
    }
  };

  const handleToggleRule = async (ruleName: string) => {
    try {
      setSaving(ruleName);
      setError(null);

      const response = await adminService.toggleRule(ruleName);

      // Update local state
      setRules((prev) =>
        prev.map((rule) =>
          rule.rule_name === ruleName ? response.rule : rule
        )
      );

      setSuccessMessage(response.message);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cambiar estado de regla');
    } finally {
      setSaving(null);
    }
  };

  const handleResetRule = (ruleName: string) => {
    setPendingChanges((prev) => {
      const { [ruleName]: _, ...rest } = prev;
      return rest;
    });
  };

  const getRuleValue = (ruleName: string): number => {
    return pendingChanges[ruleName] ?? rules.find((r) => r.rule_name === ruleName)?.rule_value ?? 0;
  };

  const formatValue = (value: number, ruleName: string): string => {
    const config = RULE_CONFIGS[ruleName];
    if (!config) return value.toString();

    if (config.unit === '%') {
      return `${(value * 100).toFixed(0)}%`;
    }
    return `${value} ${config.unit}`;
  };

  const hasPendingChanges = (ruleName: string): boolean => {
    return pendingChanges[ruleName] !== undefined;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Settings className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-600" />
          <p className="text-gray-600 dark:text-gray-400">Cargando reglas...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-5xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Configuración de Reglas de Calidad
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Administra los parámetros de calidad y límites del sistema de challenges
        </p>
      </div>

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="mb-6 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg flex items-center">
          <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 mr-3" />
          <p className="text-green-800 dark:text-green-300">{successMessage}</p>
        </div>
      )}

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mr-3" />
          <p className="text-red-800 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Rules by Category */}
      <div className="space-y-8">
        {Object.entries(RULE_CATEGORIES).map(([categoryKey, category]) => (
          <Card key={categoryKey} className="p-6">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                {category.title}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">{category.description}</p>
            </div>

            <div className="space-y-6">
              {category.rules.map((ruleName) => {
                const rule = rules.find((r) => r.rule_name === ruleName);
                const config = RULE_CONFIGS[ruleName];
                if (!rule || !config) return null;

                const currentValue = getRuleValue(ruleName);
                const isPending = hasPendingChanges(ruleName);
                const isSaving = saving === ruleName;

                return (
                  <div
                    key={ruleName}
                    className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {ruleName.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                          </h3>
                          <button
                            onClick={() => handleToggleRule(ruleName)}
                            disabled={isSaving}
                            className={`px-2 py-1 text-xs rounded ${
                              rule.is_active
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                : 'bg-gray-200 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                            }`}
                          >
                            {rule.is_active ? 'Activa' : 'Inactiva'}
                          </button>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          {config.description}
                        </p>
                      </div>
                      <div className="text-right ml-4">
                        <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                          {formatValue(currentValue, ruleName)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <input
                        type="range"
                        min={config.min}
                        max={config.max}
                        step={config.step}
                        value={currentValue}
                        onChange={(e) => handleSliderChange(ruleName, parseFloat(e.target.value))}
                        disabled={isSaving}
                        className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                      <div className="flex gap-2">
                        {isPending && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleSaveRule(ruleName)}
                              disabled={isSaving}
                              className="min-w-[80px]"
                            >
                              {isSaving ? (
                                <Settings className="w-4 h-4 animate-spin" />
                              ) : (
                                <>
                                  <Save className="w-4 h-4 mr-1" />
                                  Guardar
                                </>
                              )}
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleResetRule(ruleName)}
                              disabled={isSaving}
                            >
                              <RotateCcw className="w-4 h-4" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>{formatValue(config.min, ruleName)}</span>
                      <span>{formatValue(config.max, ruleName)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        ))}
      </div>

      {/* Info Footer */}
      <Card className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20">
        <div className="flex items-start">
          <AlertCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 mt-0.5" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-1">Información importante:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Los cambios se aplican inmediatamente al guardar</li>
              <li>Las reglas inactivas no se aplican en el sistema</li>
              <li>Los valores recomendados están basados en pruebas de rendimiento</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default PhraseRulesPage;
