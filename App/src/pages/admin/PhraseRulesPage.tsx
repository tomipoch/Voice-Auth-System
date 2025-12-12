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
import LoadingSpinner from '../../components/ui/LoadingSpinner';
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

  const filteredRules = rules.filter(rule => 
    rule.rule_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
          Reglas de Calidad
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Configuración y parámetros del sistema de frases
        </p>
      </div>

      {/* Main Content Card */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Reglas Activas</h2>
            <div className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
              {filteredRules.length}
            </div>
          </div>

          <div className="flex items-center gap-3 w-full md:w-auto">
            {/* Search Input */}
            <div className="relative flex-1 md:w-64">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-4 w-4 text-gray-400" />
              </div>
              <input 
                type="text"
                placeholder="Buscar reglas..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 h-10 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all placeholder-gray-400"
              />
            </div>

            <button
              onClick={loadRules}
              className="h-10 w-10 flex items-center justify-center rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-blue-600 dark:hover:text-blue-400 transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 shrink-0"
              title="Actualizar reglas"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Grid View (Now the only view) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRules.map((rule) => (
            <PhraseRuleCard
              key={rule.id}
              rule={rule}
              onEdit={handleEdit}
              onToggle={handleToggle}
            />
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
