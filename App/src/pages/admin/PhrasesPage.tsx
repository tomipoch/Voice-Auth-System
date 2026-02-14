/**
 * Phrases Page
 * Admin page for managing phrases with stats, filters, and table
 */

import { useState, useEffect } from 'react';
import { Search, BookOpen, Filter, Trash2 } from 'lucide-react';
import { toast } from 'react-hot-toast';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import { PhraseStatsCards } from '../../components/admin/PhraseStatsCards';
import { phraseService } from '../../services/phraseService';
import type { Phrase, Book, PhraseStats, PhraseFilters } from '../../types/phrases';

export const PhrasesPage = () => {
  const [stats, setStats] = useState<PhraseStats | null>(null);
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingTable, setLoadingTable] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filters, setFilters] = useState<PhraseFilters>({
    page: 1,
    limit: 50,
    difficulty: '',
    is_active: undefined,
    search: '',
    book_id: '',
    author: '',
  });

  const [totalPages, setTotalPages] = useState(1);
  const [totalPhrases, setTotalPhrases] = useState(0);

  // Load stats and books on mount
  useEffect(() => {
    loadStats();
    loadBooks();
  }, []);

  // Load phrases when filters change
  useEffect(() => {
    loadPhrases();
  }, [filters]);

  const loadStats = async () => {
    try {
      const data = await phraseService.getStats();
      setStats(data);
    } catch (err) {
      console.error('Error loading stats:', err);
      toast.error('Error al cargar estadísticas');
    } finally {
      setLoading(false);
    }
  };

  const loadBooks = async () => {
    try {
      const data = await phraseService.getBooks();
      setBooks(data);
    } catch (err) {
      console.error('Error loading books:', err);
    }
  };

  const loadPhrases = async () => {
    setLoadingTable(true);
    setError(null);
    try {
      const response = await phraseService.getPhrases(filters);
      setPhrases(response.phrases);
      setTotalPages(response.total_pages);
      setTotalPhrases(response.total);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Error al cargar frases';
      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoadingTable(false);
    }
  };

  const handleToggleStatus = async (phraseId: string, currentStatus: boolean) => {
    try {
      await phraseService.togglePhraseStatus(phraseId, !currentStatus);
      toast.success(`Frase ${!currentStatus ? 'activada' : 'desactivada'}`);

      // Update local state
      setPhrases((prev) =>
        prev.map((p) => (p.id === phraseId ? { ...p, is_active: !currentStatus } : p))
      );

      // Reload stats
      loadStats();
    } catch (err) {
      toast.error('Error al cambiar estado de la frase');
    }
  };

  const handleDelete = async (phraseId: string) => {
    if (!confirm('¿Estás seguro de eliminar esta frase?')) return;

    try {
      await phraseService.deletePhrase(phraseId);
      toast.success('Frase eliminada');

      // Remove from local state
      setPhrases((prev) => prev.filter((p) => p.id !== phraseId));

      // Reload stats
      loadStats();
    } catch (err) {
      toast.error('Error al eliminar frase');
    }
  };

  const handleFilterChange = (key: keyof PhraseFilters, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value, page: 1 }));
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  const getDifficultyBadge = (difficulty: string) => {
    const colors: Record<string, string> = {
      easy: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
      hard: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  // Get unique authors
  const uniqueAuthors = Array.from(new Set(books.map((b) => b.author).filter(Boolean)));

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Gestión de Frases
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Administra las {stats?.total.toLocaleString() || '...'} frases del sistema
        </p>
      </div>

      {/* Stats Cards */}
      <PhraseStatsCards stats={stats} loading={loading} />

      {/* Filters Card */}
      <Card className="p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Filtros</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar en frases..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              value={filters.search || ''}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>

          {/* Difficulty */}
          <select
            value={filters.difficulty || ''}
            onChange={(e) => handleFilterChange('difficulty', e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="">Todas las dificultades</option>
            <option value="easy">🟢 Fácil</option>
            <option value="medium">🟡 Media</option>
            <option value="hard">🔴 Difícil</option>
          </select>

          {/* Status */}
          <select
            value={filters.is_active === undefined ? '' : filters.is_active.toString()}
            onChange={(e) => {
              const value = e.target.value === '' ? undefined : e.target.value === 'true';
              handleFilterChange('is_active', value);
            }}
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="">Todos los estados</option>
            <option value="true">✅ Activas</option>
            <option value="false">❌ Inactivas</option>
          </select>

          {/* Book */}
          <select
            value={filters.book_id || ''}
            onChange={(e) => handleFilterChange('book_id', e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="">Todos los libros ({books.length})</option>
            {books.map((book) => (
              <option key={book.id} value={book.id}>
                📖 {book.title}
              </option>
            ))}
          </select>

          {/* Author */}
          <select
            value={filters.author || ''}
            onChange={(e) => handleFilterChange('author', e.target.value)}
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
          >
            <option value="">Todos los autores ({uniqueAuthors.length})</option>
            {uniqueAuthors.map((author) => (
              <option key={author} value={author}>
                ✍️ {author}
              </option>
            ))}
          </select>

          {/* Clear Filters */}
          <button
            onClick={() =>
              setFilters({
                page: 1,
                limit: 50,
                difficulty: '',
                is_active: undefined,
                search: '',
                book_id: '',
                author: '',
              })
            }
            className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            🔄 Limpiar filtros
          </button>
        </div>

        {/* Active Filters Summary */}
        {(filters.search || filters.difficulty || filters.is_active !== undefined || filters.book_id || filters.author) && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Mostrando <span className="font-semibold text-gray-900 dark:text-gray-100">{totalPhrases.toLocaleString()}</span> resultados
              {filters.search && ` con "${filters.search}"`}
              {filters.difficulty && ` • Dificultad: ${filters.difficulty}`}
              {filters.is_active !== undefined && ` • ${filters.is_active ? 'Activas' : 'Inactivas'}`}
              {filters.book_id && ` • Libro seleccionado`}
              {filters.author && ` • Autor: ${filters.author}`}
            </p>
          </div>
        )}
      </Card>

      {/* Table Card */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Frases</h2>
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Página {filters.page} de {totalPages}
          </div>
        </div>

        {error ? (
          <EmptyState
            icon={<BookOpen className="h-16 w-16" />}
            title="Error al cargar frases"
            description={error}
          />
        ) : loadingTable ? (
          <LoadingSpinner size="lg" text="Cargando frases..." className="py-12" />
        ) : phrases.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="h-16 w-16" />}
            title="No se encontraron frases"
            description="No hay frases que coincidan con los filtros aplicados."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Texto
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Dificultad
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Palabras
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Estado
                    </th>
                    <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                  {phrases.map((phrase) => (
                    <tr
                      key={phrase.id}
                      className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className="max-w-md">
                          <p className="font-medium text-gray-900 dark:text-gray-100 line-clamp-2">
                            {phrase.text}
                          </p>
                          {(phrase.book_title || phrase.source) && (
                            <p className="text-xs text-gray-600 dark:text-gray-300 mt-1">
                              📚 {phrase.book_title || phrase.source}
                              {phrase.book_author && ` - ${phrase.book_author}`}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium capitalize ${getDifficultyBadge(
                            phrase.difficulty
                          )}`}
                        >
                          {phrase.difficulty}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="text-sm text-gray-600 dark:text-gray-300">
                          {phrase.word_count}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div
                          onClick={() => handleToggleStatus(phrase.id, phrase.is_active)}
                          className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                            phrase.is_active
                              ? 'bg-green-500 hover:bg-green-600'
                              : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
                          }`}
                          style={{ width: '44px', height: '24px', borderRadius: '9999px' }}
                          title={phrase.is_active ? 'Desactivar frase' : 'Activar frase'}
                        >
                          <span
                            className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                              phrase.is_active ? 'translate-x-5' : 'translate-x-0'
                            }`}
                            style={{ width: '20px', height: '20px' }}
                          />
                        </div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center">
                        <button
                          onClick={() => handleDelete(phrase.id)}
                          className="flex items-center justify-center h-8 w-8 rounded-full bg-red-100 text-red-600 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50 transition-colors"
                          title="Eliminar frase"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="mt-6 flex items-center justify-between border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Mostrando {((filters.page! - 1) * filters.limit!) + 1} - {Math.min(filters.page! * filters.limit!, totalPhrases)} de {totalPhrases.toLocaleString()} frases
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePageChange(filters.page! - 1)}
                  disabled={filters.page === 1}
                  className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  ← Anterior
                </button>
                <button
                  onClick={() => handlePageChange(filters.page! + 1)}
                  disabled={filters.page === totalPages}
                  className="px-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  Siguiente →
                </button>
              </div>
            </div>
          </>
        )}
      </Card>
    </MainLayout>
  );
};

export default PhrasesPage;
