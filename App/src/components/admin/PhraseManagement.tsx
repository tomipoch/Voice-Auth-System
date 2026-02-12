import React, { useState, useEffect, useCallback } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import { phraseService } from '../../services/apiServices';
import type { Phrase, PhraseStats } from '../../types';

export const PhraseManagement: React.FC = () => {
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [stats, setStats] = useState<PhraseStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const phrasesPerPage = 20;

  const fetchStats = async () => {
    try {
      const data = await phraseService.getStats();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  };

  const fetchPhrases = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const difficulty = selectedDifficulty === 'all' ? undefined : selectedDifficulty;
      const data = await phraseService.listPhrases(difficulty, 'es', 1000);
      setPhrases(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, [selectedDifficulty]);

  useEffect(() => {
    fetchStats();
    fetchPhrases();
  }, [fetchPhrases]);

  const handleToggleActive = async (phraseId: string, currentStatus: boolean) => {
    try {
      await phraseService.updateStatus(phraseId, !currentStatus);

      // Actualizar localmente
      setPhrases((prev) =>
        prev.map((p) => (p.id === phraseId ? { ...p, is_active: !currentStatus } : p))
      );

      // Actualizar estadísticas
      fetchStats();
    } catch (err) {
      console.error('Error toggling phrase:', err);
      alert('Error al actualizar la frase');
    }
  };

  const handleDelete = async (phraseId: string) => {
    if (!confirm('¿Estás seguro de eliminar esta frase?')) return;

    try {
      await phraseService.deletePhrase(phraseId);

      // Eliminar localmente
      setPhrases((prev) => prev.filter((p) => p.id !== phraseId));

      // Actualizar estadísticas
      fetchStats();
    } catch (err) {
      console.error('Error deleting phrase:', err);
      alert('Error al eliminar la frase');
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'hard':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  // Paginación
  const indexOfLastPhrase = currentPage * phrasesPerPage;
  const indexOfFirstPhrase = indexOfLastPhrase - phrasesPerPage;
  const currentPhrases = phrases.slice(indexOfFirstPhrase, indexOfLastPhrase);
  const totalPages = Math.ceil(phrases.length / phrasesPerPage);

  if (loading && phrases.length === 0) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Estadísticas */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Total</h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
          </Card>
          <Card className="p-4">
            <h3 className="text-sm font-medium text-green-600 dark:text-green-400">Fáciles</h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.easy}</p>
          </Card>
          <Card className="p-4">
            <h3 className="text-sm font-medium text-yellow-600 dark:text-yellow-400">Medias</h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.medium}</p>
          </Card>
          <Card className="p-4">
            <h3 className="text-sm font-medium text-red-600 dark:text-red-400">Difíciles</h3>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{stats.hard}</p>
          </Card>
        </div>
      )}

      {/* Filtros */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex gap-2">
            <Button
              variant={selectedDifficulty === 'all' ? 'primary' : 'secondary'}
              onClick={() => setSelectedDifficulty('all')}
              size="sm"
            >
              Todas
            </Button>
            <Button
              variant={selectedDifficulty === 'easy' ? 'primary' : 'secondary'}
              onClick={() => setSelectedDifficulty('easy')}
              size="sm"
            >
              Fáciles
            </Button>
            <Button
              variant={selectedDifficulty === 'medium' ? 'primary' : 'secondary'}
              onClick={() => setSelectedDifficulty('medium')}
              size="sm"
            >
              Medias
            </Button>
            <Button
              variant={selectedDifficulty === 'hard' ? 'primary' : 'secondary'}
              onClick={() => setSelectedDifficulty('hard')}
              size="sm"
            >
              Difíciles
            </Button>
          </div>
          <Button onClick={fetchPhrases} size="sm">
            🔄 Actualizar
          </Button>
        </div>
      </Card>

      {/* Lista de frases */}
      {error && (
        <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </Card>
      )}

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Frase
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Origen
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Dificultad
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Palabras
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {currentPhrases.map((phrase) => (
                <tr key={phrase.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-6 py-4">
                    <p className="text-sm text-gray-900 dark:text-gray-100 max-w-md truncate">
                      {phrase.text}
                    </p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {phrase.source || 'N/A'}
                    </p>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getDifficultyColor(phrase.difficulty)}`}
                    >
                      {phrase.difficulty}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                    {phrase.word_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        phrase.is_active
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {phrase.is_active ? 'Activa' : 'Inactiva'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => handleToggleActive(phrase.id, phrase.is_active)}
                      className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                      title={phrase.is_active ? 'Desactivar' : 'Activar'}
                    >
                      {phrase.is_active ? '⏸️' : '▶️'}
                    </button>
                    <button
                      onClick={() => handleDelete(phrase.id)}
                      className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                      title="Eliminar"
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {totalPages > 1 && (
          <div className="px-6 py-4 flex items-center justify-between border-t border-gray-200 dark:border-gray-700">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              Mostrando {indexOfFirstPhrase + 1} a {Math.min(indexOfLastPhrase, phrases.length)} de{' '}
              {phrases.length} frases
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                size="sm"
                variant="secondary"
              >
                Anterior
              </Button>
              <span className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                Página {currentPage} de {totalPages}
              </span>
              <Button
                onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                size="sm"
                variant="secondary"
              >
                Siguiente
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
