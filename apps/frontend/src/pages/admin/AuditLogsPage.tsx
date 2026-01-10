import { useState, useEffect } from 'react';
import {
  FileText,
  Search,
  Filter,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Download,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import Select from '../../components/ui/Select';
import Input from '../../components/ui/Input';
import adminService, { type AuditLog } from '../../services/adminService';
import toast from 'react-hot-toast';

const AuditLogsPage = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const data = await adminService.getLogs(100);
      setLogs(data);
    } catch (error) {
      console.error('Error fetching logs:', error);
      toast.error('Error al cargar logs de auditoría');
    } finally {
      setLoading(false);
    }
  };

  const getLevelFromAction = (action: string): string => {
    const actionLower = action.toLowerCase();
    if (actionLower.includes('error') || actionLower.includes('failed')) return 'error';
    if (actionLower.includes('warning') || actionLower.includes('attempt')) return 'warning';
    if (actionLower.includes('success') || actionLower.includes('verification')) return 'success';
    return 'info';
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info':
        return <Info className="h-4 w-4 text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-600 dark:text-gray-300" aria-hidden="true" />;
    }
  };

  const getLevelClass = (level: string) => {
    switch (level) {
      case 'info':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'success':
        return 'bg-green-50 text-green-700 border-green-200';
      case 'warning':
        return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'error':
        return 'bg-red-50 text-red-700 border-red-200';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  const filteredLogs = logs.filter((log) => {
    const level = getLevelFromAction(log.action);
    const matchesFilter = filter === 'all' || level === filter;
    const matchesSearch =
      searchTerm === '' ||
      log.user_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.details.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  const handleExport = async () => {
    setExporting(true);
    try {
      await adminService.exportActivity(30);
      toast.success('Actividad exportada correctamente');
    } catch (error) {
      console.error('Error exporting activity:', error);
      toast.error('Error al exportar actividad');
    } finally {
      setExporting(false);
    }
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Logs de Auditoría
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300">
          Registro detallado de eventos y actividades del sistema
        </p>
      </div>

      <Card className="p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1 w-full">
            <Input
              placeholder="Buscar por usuario, acción o detalles..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400"
              aria-hidden="true"
            />
          </div>
          <div className="flex items-center gap-4 w-full md:w-auto">
            <div className="relative flex-1 md:w-48">
              <Select value={filter} onChange={(e) => setFilter(e.target.value)} className="pl-10">
                <option value="all">Todos los niveles</option>
                <option value="success">Éxito</option>
                <option value="info">Información</option>
                <option value="warning">Advertencia</option>
                <option value="error">Error</option>
              </Select>
              <Filter
                className="absolute left-3 bottom-[14px] h-4 w-4 text-gray-400"
                aria-hidden="true"
              />
            </div>
            <button
              onClick={handleExport}
              disabled={exporting}
              className="h-11 w-11 flex items-center justify-center rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-700 transition-all shrink-0 focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50 shadow-sm"
              title="Exportar Actividad (CSV)"
            >
              <Download className={`h-5 w-5 ${exporting ? 'animate-bounce text-blue-500' : ''}`} />
            </button>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        {/* Logs Table */}
        {loading ? (
          <LoadingSpinner size="lg" text="Cargando logs..." className="py-12" />
        ) : filteredLogs.length === 0 ? (
          <EmptyState
            icon={<FileText className="h-16 w-16" />}
            title="No se encontraron logs"
            description="No hay registros de auditoría que coincidan con tus filtros. Intenta ajustar los criterios de búsqueda."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                    Timestamp
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                    Nivel
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                    Acción
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                    Usuario
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700 dark:text-gray-300">
                    Detalles
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {filteredLogs.map((log) => {
                  const level = getLevelFromAction(log.action);
                  return (
                    <tr
                      key={log.id}
                      className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 font-mono text-xs md:text-sm"
                    >
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-300 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-1 rounded border ${getLevelClass(level)}`}
                        >
                          {getLevelIcon(level)}
                          <span className="ml-1 uppercase font-bold text-[10px]">{level}</span>
                        </span>
                      </td>
                      <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">
                        {log.action}
                      </td>
                      <td className="py-3 px-4 text-blue-600 dark:text-blue-400">
                        {log.user_name}
                      </td>
                      <td
                        className="py-3 px-4 text-gray-700 dark:text-gray-300 max-w-xs truncate"
                        title={log.details}
                      >
                        {log.details}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </MainLayout>
  );
};

export default AuditLogsPage;
