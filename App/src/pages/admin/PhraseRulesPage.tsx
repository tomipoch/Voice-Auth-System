/**
 * Phrase Rules Page
 * Admin page for managing phrase quality rules
 */

import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import type { PhraseRule } from '../../types/phraseRules';
import { phraseRulesService } from '../../services/phraseRulesService';
import { PhraseRuleCard } from '../../components/admin/PhraseRuleCard';
import { PhraseRuleEditor } from '../../components/admin/PhraseRuleEditor';
import MainLayout from '../../components/ui/MainLayout';

export const PhraseRulesPage = () => {
  const [rules, setRules] = useState<PhraseRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRule, setSelectedRule] = useState<PhraseRule | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);

  // Load rules on mount
  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await phraseRulesService.getRules(true); // Include inactive
      setRules(data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Error al cargar las reglas';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (rule: PhraseRule) => {
    setSelectedRule(rule);
    setIsEditorOpen(true);
  };

  const handleSave = async (ruleName: string, newValue: number) => {
    try {
      const response = await phraseRulesService.updateRule(ruleName, newValue);
      toast.success(response.message || 'Regla actualizada correctamente');

      // Update local state
      setRules((prevRules) =>
        prevRules.map((rule) =>
          rule.rule_name === ruleName
            ? { ...rule, rule_value: newValue, updated_at: new Date().toISOString() }
            : rule
        )
      );
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Error al actualizar la regla';
      toast.error(errorMessage);
      throw err; // Re-throw to let modal handle it
    }
  };

  const handleToggle = async (ruleName: string, isActive: boolean) => {
    try {
      const response = await phraseRulesService.toggleRule(ruleName, isActive);
      toast.success(response.message || `Regla ${isActive ? 'activada' : 'desactivada'}`);

      // Update local state
      setRules((prevRules) =>
        prevRules.map((rule) =>
          rule.rule_name === ruleName
            ? { ...rule, is_active: isActive, updated_at: new Date().toISOString() }
            : rule
        )
      );
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Error al cambiar el estado de la regla';
      toast.error(errorMessage);
    }
  };

  const handleCloseEditor = () => {
    setIsEditorOpen(false);
    setSelectedRule(null);
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          ⚙️ Configuración de Reglas de Calidad
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Gestiona las reglas que controlan el comportamiento del sistema de frases
        </p>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
              <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-5/6"></div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="text-red-600 text-lg font-medium mb-2">
            ⚠️ Error al cargar las reglas
          </div>
          <p className="text-red-500 mb-4">{error}</p>
          <button
            onClick={loadRules}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Reintentar
          </button>
        </div>
      )}

      {/* Rules Grid */}
      {!isLoading && !error && rules.length > 0 && (
        <>
          <div className="mb-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Mostrando {rules.length} regla{rules.length !== 1 ? 's' : ''}
            </div>
            <button
              onClick={loadRules}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              🔄 Actualizar
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {rules.map((rule) => (
              <PhraseRuleCard
                key={rule.id}
                rule={rule}
                onEdit={handleEdit}
                onToggle={handleToggle}
              />
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!isLoading && !error && rules.length === 0 && (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="text-gray-400 text-6xl mb-4">📋</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No hay reglas configuradas</h3>
          <p className="text-gray-600">
            Las reglas de calidad se configuran automáticamente al inicializar el sistema
          </p>
        </div>
      )}

      {/* Editor Modal */}
      <PhraseRuleEditor
        rule={selectedRule}
        isOpen={isEditorOpen}
        onClose={handleCloseEditor}
        onSave={handleSave}
      />
    </MainLayout>
  );
};

export default PhraseRulesPage;
