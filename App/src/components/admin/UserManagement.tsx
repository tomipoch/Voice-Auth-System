import { useState } from 'react';
import {
  Users,
  Shield,
  Activity,
  AlertTriangle,
  Search,
  Filter,
  Edit,
  Trash2,
  Eye,
} from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import StatusIndicator from '../ui/StatusIndicator';
import { User } from '../../types';

interface UserManagementProps {
  users?: User[];
  onUserAction?: (action: string, userId: string) => void;
  isLoading?: boolean;
}

const UserManagement = ({ users = [], onUserAction, isLoading = false }: UserManagementProps) => {
  const [searchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [currentPage] = useState(1);
  const [, setCurrentPage] = useState(1);

  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      (user?.fullName || user?.username || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      selectedFilter === 'all' ||
      (selectedFilter === 'active' && user.isVerified) ||
      (selectedFilter === 'inactive' && !user.isVerified) ||
      (selectedFilter === 'enrolled' && user.voiceProfile) ||
      (selectedFilter === 'pending' && !user.voiceProfile);

    return matchesSearch && matchesFilter;
  });

  const getUserStatus = (user: User): string => {
    if (!user.isVerified) return 'inactive';
    if (!user.voiceProfile) return 'pending';
    return 'active';
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'pending' => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'pending';
    }
  };

  const handleSelectUser = (userId: string) => {
    setSelectedUsers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    if (selectedUsers.length === filteredUsers.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(filteredUsers.map((user) => user.id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Estadísticas generales */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center">
            <div className="shrink-0">
              <Users className="h-8 w-8 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Total Usuarios</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {users.length}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center">
            <div className="shrink-0">
              <Shield className="h-8 w-8 text-green-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Registrados</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {users.filter((u) => u.voiceProfile).length}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center">
            <div className="shrink-0">
              <Activity className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Activos</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {users.filter((u) => u.isVerified).length}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center">
            <div className="shrink-0">
              <AlertTriangle className="h-8 w-8 text-yellow-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300">Pendientes</p>
              <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {users.filter((u) => !u.voiceProfile).length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Controles de búsqueda y filtros */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0 sm:space-x-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <Input
                type="number"
                value={currentPage.toString()}
                onChange={(e) => setCurrentPage(parseInt(e.target.value) || 1)}
                className="w-16 text-center"
              />
            </div>
          </div>

          <div className="flex items-center space-x-3">
            \n{' '}
            <div className="relative">
              <Filter className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">Todos</option>
                <option value="active">Activos</option>
                <option value="inactive">Inactivos</option>
                <option value="enrolled">Registrados</option>
                <option value="pending">Pendientes</option>
              </select>
            </div>
            {selectedUsers.length > 0 && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => onUserAction && onUserAction('bulk-delete', selectedUsers.join(','))}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Eliminar ({selectedUsers.length})
              </Button>
            )}
          </div>
        </div>
      </Card>

      {/* Tabla de usuarios */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={
                      selectedUsers.length === filteredUsers.length && filteredUsers.length > 0
                    }
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Usuario
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Estado
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Perfil de Voz
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Último Acceso
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-300 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center">
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <span className="ml-2 text-gray-700 dark:text-gray-300">
                        Cargando usuarios...
                      </span>
                    </div>
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-6 py-12 text-center text-gray-600 dark:text-gray-300"
                  >
                    No se encontraron usuarios
                  </td>
                </tr>
              ) : (
                filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 dark:bg-gray-800">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedUsers.includes(user.id)}
                        onChange={() => handleSelectUser(user.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 shrink-0">
                          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <span className="text-sm font-medium text-blue-600">
                            {(user?.fullName || user?.username || 'U').charAt(0).toUpperCase()}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {user.fullName || user.username}
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-300">
                            {user.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusIndicator
                        status={getStatusColor(getUserStatus(user))}
                        message={
                          getUserStatus(user) === 'active'
                            ? 'Activo'
                            : getUserStatus(user) === 'inactive'
                              ? 'Inactivo'
                              : 'Pendiente'
                        }
                        size="sm"
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                      {user.voiceProfile ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Registrado
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          Sin registrar
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-300">
                      {user.updatedAt ? new Date(user.updatedAt).toLocaleDateString() : 'Nunca'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onUserAction?.('view', user.id)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onUserAction?.('edit', user.id)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onUserAction?.('delete', user.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

export default UserManagement;
