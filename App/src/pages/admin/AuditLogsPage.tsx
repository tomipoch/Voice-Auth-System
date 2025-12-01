import { useState } from 'react';
import { FileText, Search, Filter, AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';

// Mock data
const mockLogs = [
  { id: 1, timestamp: '2024-11-30 14:35:22', level: 'info', action: 'User Login', user: 'juan.perez@example.com', details: 'Successful login from IP 192.168.1.1' },
  { id: 2, timestamp: '2024-11-30 14:30:15', level: 'success', action: 'Verification', user: 'juan.perez@example.com', details: 'Voice verification successful (Score: 98%)' },
  { id: 3, timestamp: '2024-11-30 12:10:05', level: 'warning', action: 'Failed Login', user: 'maria.gomez@example.com', details: 'Invalid password attempt 2' },
  { id: 4, timestamp: '2024-11-30 10:00:00', level: 'error', action: 'System Error', user: 'system', details: 'Database connection timeout (retried)' },
  { id: 5, timestamp: '2024-11-29 18:45:30', level: 'info', action: 'User Created', user: 'admin@company.com', details: 'New user "Pedro Lopez" created' },
];

const AuditLogsPage = () => {
  const [logs] = useState(mockLogs);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');

  const getLevelIcon = (level) => {
    switch (level) {
      case 'info': return <Info className="h-4 w-4 text-blue-500" />;
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getLevelClass = (level) => {
    switch (level) {
      case 'info': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'success': return 'bg-green-50 text-green-700 border-green-200';
      case 'warning': return 'bg-yellow-50 text-yellow-700 border-yellow-200';
      case 'error': return 'bg-red-50 text-red-700 border-red-200';
      default: return 'bg-gray-50 text-gray-700 border-gray-200';
    }
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Logs de Auditoría
        </h1>
        <p className="text-lg text-gray-500 dark:text-gray-400">
          Registro detallado de eventos y actividades del sistema
        </p>
      </div>

      <Card className="p-6">
        {/* Filters */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
          <div className="relative w-full md:w-96">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por usuario, acción o detalles..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <select
              className="border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            >
              <option value="all">Todos los Niveles</option>
              <option value="info">Info</option>
              <option value="success">Success</option>
              <option value="warning">Warning</option>
              <option value="error">Error</option>
            </select>
          </div>
        </div>

        {/* Logs Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-800/50 border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 font-semibold text-gray-600 dark:text-gray-400">Timestamp</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600 dark:text-gray-400">Nivel</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600 dark:text-gray-400">Acción</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600 dark:text-gray-400">Usuario</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-600 dark:text-gray-400">Detalles</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 font-mono text-xs md:text-sm">
                  <td className="py-3 px-4 text-gray-500 whitespace-nowrap">{log.timestamp}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded border ${getLevelClass(log.level)}`}>
                      {getLevelIcon(log.level)}
                      <span className="ml-1 uppercase font-bold text-[10px]">{log.level}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 font-medium text-gray-800 dark:text-gray-200">{log.action}</td>
                  <td className="py-3 px-4 text-blue-600 dark:text-blue-400">{log.user}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400 max-w-xs truncate" title={log.details}>
                    {log.details}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </MainLayout>
  );
};

export default AuditLogsPage;
