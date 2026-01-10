import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Search,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  Calendar,
  Download,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { superadminService } from '../../services/superadminService';
import type { AuditLogEntry, CompanyStats } from '../../services/superadminService';
import toast from 'react-hot-toast';

const GlobalAuditPage = () => {
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [companies, setCompanies] = useState<CompanyStats[]>([]);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCompany, setFilterCompany] = useState<string>('');
  const [filterAction, setFilterAction] = useState<string>('');
  const [filterSuccess, setFilterSuccess] = useState<string>('');
  const [page, setPage] = useState(1);
  const logsPerPage = 20;

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const data = await superadminService.getAuditLogs({
        limit: 500,
        company: filterCompany || undefined,
        action: filterAction || undefined,
      });
      setLogs(data);
    } catch (error) {
      console.error('Error loading audit logs:', error);
      toast.error('Error al cargar logs de auditoría');
    } finally {
      setLoading(false);
    }
  }, [filterCompany, filterAction]);

  useEffect(() => {
    loadData();
    superadminService.getCompanies().then(setCompanies).catch(console.error);
  }, [loadData]);

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.actor.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.details?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesSuccess =
      filterSuccess === '' ||
      (filterSuccess === 'true' && log.success) ||
      (filterSuccess === 'false' && !log.success);

    return matchesSearch && matchesSuccess;
  });

  // Paginated logs
  const paginatedLogs = filteredLogs.slice((page - 1) * logsPerPage, page * logsPerPage);
  const totalPagesCount = Math.ceil(filteredLogs.length / logsPerPage);

  const exportToCSV = () => {
    const headers = ['Fecha', 'Actor', 'Acción', 'Empresa', 'Éxito', 'Detalles'];
    const rows = filteredLogs.map((log) => [
      new Date(log.timestamp).toISOString(),
      log.actor,
      log.action,
      log.company || '',
      log.success ? 'Sí' : 'No',
      log.details || '',
    ]);

    const csv = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Logs exportados correctamente');
  };

  const actionTypes = [...new Set(logs.map((l) => l.action))].sort();

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Auditoría Global
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Logs de actividad de todo el sistema
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Total Logs</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{logs.length}</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-600">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Exitosos</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {logs.filter((l) => l.success).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600">
              <XCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Fallidos</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {logs.filter((l) => !l.success).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Acciones Únicas</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {actionTypes.length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card className="p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <Input
              placeholder="Buscar por actor, acción o detalles..."
              icon={<Search className="h-4 w-4" />}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Company Filter */}
          <Select value={filterCompany} onChange={(e) => setFilterCompany(e.target.value)}>
            <option value="">Todas las empresas</option>
            {companies.map((c, i) => (
              <option key={i} value={c.name}>
                {c.name}
              </option>
            ))}
          </Select>

          {/* Action Filter */}
          <Select value={filterAction} onChange={(e) => setFilterAction(e.target.value)}>
            <option value="">Todas las acciones</option>
            {actionTypes.map((action, i) => (
              <option key={i} value={action}>
                {action}
              </option>
            ))}
          </Select>

          {/* Success Filter */}
          <Select value={filterSuccess} onChange={(e) => setFilterSuccess(e.target.value)}>
            <option value="">Todos los estados</option>
            <option value="true">Exitosos</option>
            <option value="false">Fallidos</option>
          </Select>

          <div className="flex gap-2 ml-auto">
            <Button variant="secondary" onClick={loadData} className="h-12">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button variant="success" onClick={exportToCSV} className="h-12">
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Logs Table */}
      <Card className="p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Fecha/Hora
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Actor
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Acción
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Empresa
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Estado
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Detalles
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {paginatedLogs.map((log) => (
                  <tr key={log.timestamp} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                    <td className="py-3 px-4 text-sm text-gray-500">
                      <div>{new Date(log.timestamp).toLocaleDateString()}</div>
                      <div className="text-xs">{new Date(log.timestamp).toLocaleTimeString()}</div>
                    </td>
                    <td className="py-3 px-4 text-sm font-medium text-gray-900 dark:text-gray-100">
                      {log.actor}
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">
                      {log.company || '-'}
                    </td>
                    <td className="py-3 px-4">
                      {log.success ? (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                          <CheckCircle className="h-3 w-3 mr-1" />
                          OK
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                          <XCircle className="h-3 w-3 mr-1" />
                          Error
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500 max-w-xs truncate">
                      {log.details || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredLogs.length === 0 && (
              <div className="text-center py-12 text-gray-500">No se encontraron logs</div>
            )}
          </div>
        )}

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <span className="text-sm text-gray-500">
            Mostrando {Math.min((page - 1) * logsPerPage + 1, filteredLogs.length)}-
            {Math.min(page * logsPerPage, filteredLogs.length)} de {filteredLogs.length} logs
          </span>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Anterior
            </Button>
            <span className="px-3 py-1 text-sm text-gray-600 dark:text-gray-300">
              Página {page} de {totalPagesCount}
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= totalPagesCount}
              onClick={() => setPage((p) => p + 1)}
            >
              Siguiente
            </Button>
          </div>
        </div>
      </Card>
    </MainLayout>
  );
};

export default GlobalAuditPage;
