/**
 * Phrase Rules Page
 * Admin page for managing phrase quality rules
 */

import { useState, useEffect } from 'react';
import { Settings, RefreshCw, Search } from 'lucide-react';
import { toast } from 'react-hot-toast';
import type { PhraseRule } from '../../types/phraseRules';
import { phraseRulesService } from '../../services/phraseRulesService';
import { PhraseRuleCard } from '../../components/admin/PhraseRuleCard';
import { PhraseRuleEditor } from '../../components/admin/PhraseRuleEditor';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Input from '../../components/ui/Input';
import EmptyState from '../../components/ui/EmptyState';

export const PhraseRulesPage = () => {
  const [rules, setRules] = useState<PhraseRule[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRule, setSelectedRule] = useState<PhraseRule | null>(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Load rules on mount
  useEffect(() => {
    loadRules();
  }, []);

  const filteredRules = rules.filter(
    (rule) =>
      rule.rule_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const loadRules = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await phraseRulesService.getRules(true); // Include inactive
      setRules(data);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const errorMessage = axiosError.response?.data?.detail || 'Error al cargar las reglas';
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
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const errorMessage = axiosError.response?.data?.detail || 'Error al actualizar la regla';
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
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { detail?: string } } };
      const errorMessage =
        axiosError.response?.data?.detail || 'Error al cambiar el estado de la regla';
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
          Reglas de Calidad
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Configuración y parámetros del sistema de frases
        </p>
      </div>

      {/* Search and Controls Card */}
      <Card className="p-4 mb-6">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Input
              placeholder="Buscar reglas por nombre o descripción..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label="Buscar reglas de calidad"
            />
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400"
              aria-hidden="true"
            />
          </div>

          <button
            onClick={loadRules}
            disabled={isLoading}
            className="h-11 w-11 flex items-center justify-center rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-700 transition-all shrink-0 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 shadow-sm"
            title="Actualizar reglas"
          >
            <RefreshCw className={`h-5 w-5 ${isLoading ? 'animate-spin text-blue-500' : ''}`} />
          </button>
        </div>
      </Card>

      {/* Rules Grid Card */}
      <Card className="p-6">
        {/* Grid View */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRules.map((rule) => (
            <PhraseRuleCard key={rule.id} rule={rule} onEdit={handleEdit} onToggle={handleToggle} />
          ))}
        </div>
      </Card>

      {/* Empty State */}
      {!isLoading && !error && filteredRules.length === 0 && (
        <Card className="p-6">
          <EmptyState
            icon={<Settings className="h-16 w-16" />}
            title="No hay reglas configuradas"
            description="Las reglas de calidad se configuran automáticamente al inicializar el sistema"
          />
        </Card>
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
