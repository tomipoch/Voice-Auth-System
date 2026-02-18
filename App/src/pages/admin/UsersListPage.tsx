import { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Mic,
  AlertTriangle,
  ChevronRight,
  Key,
  UserX,
  UserCheck,
  X,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import LoadingSpinner from '../../components/ui/LoadingSpinner';
import EmptyState from '../../components/ui/EmptyState';
import toast from 'react-hot-toast';
import adminService, { type AdminUser } from '../../services/adminService';

const UsersListPage = () => {
  const navigate = useNavigate();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'reset' | 'toggle';
    user: AdminUser;
  } | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const data = await adminService.getUsers();
      setUsers(data.users);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Error al cargar usuarios');
    } finally {
      setLoadingUsers(false);
    }
  };

  const filteredUsers = users.filter((user) =>
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleResetPassword = (user: AdminUser) => {
    setConfirmAction({ type: 'reset', user });
    setShowConfirmModal(true);
  };

  const handleToggleStatus = (user: AdminUser) => {
    setConfirmAction({ type: 'toggle', user });
    setShowConfirmModal(true);
  };

  const handleConfirmAction = async () => {
    if (!confirmAction) return;

    try {
      if (confirmAction.type === 'reset') {
        // TODO: Implement password reset endpoint when available
        console.log('Reset password for', confirmAction.user.id);
        toast.success('Contraseña reseteada exitosamente');
      } else {
        // Toggle user status using the new updateUser endpoint
        const newStatus = confirmAction.user.status === 'active' ? 'inactive' : 'active';
        await adminService.updateUser(confirmAction.user.id, { status: newStatus });
        toast.success(
          `Usuario ${newStatus === 'active' ? 'activado' : 'desactivado'} exitosamente`
        );
      }
      setShowConfirmModal(false);
      setConfirmAction(null);
      // Refresh users list
      await fetchUsers();
    } catch (error) {
      console.error('Error performing action:', error);
      toast.error('Error al realizar la acción');
    }
  };

  return (
    <MainLayout>
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Gestión de Usuarios
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Administra los usuarios de tu empresa
        </p>
      </div>

      <Card className="p-6">
        <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Usuarios</h2>
          <div className="relative w-full md:w-64">
            <Search
              className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400"
              aria-hidden="true"
            />
            <input
              type="text"
              placeholder="Buscar usuario..."
              className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              aria-label="Buscar usuarios por email"
            />
          </div>
        </div>

        {loadingUsers ? (
          <LoadingSpinner size="lg" text="Cargando usuarios..." className="py-12" />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full" role="table" aria-label="Lista de usuarios">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Usuario
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Rol
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Estado
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Biometría
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {filteredUsers.map((u) => (
                  <tr
                    key={u.id}
                    className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/admin/users/${u.id}`)}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        <div className="h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 font-bold mr-3">
                          {u.email.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">{u.email}</p>
                          <p className="text-xs text-gray-600 dark:text-gray-300">
                            ID: {u.id.substring(0, 8)}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300 capitalize">
                        {u.role}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium capitalize ${
                          u.status === 'active'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        {u.status === 'active' ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {u.enrollment_status === 'enrolled' ? (
                        <span className="flex items-center text-green-600 text-sm">
                          <Mic className="h-3 w-3 mr-1" aria-hidden="true" /> Activo
                        </span>
                      ) : (
                        <span className="flex items-center text-orange-500 text-sm">
                          <AlertTriangle className="h-3 w-3 mr-1" aria-hidden="true" /> Pendiente
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleResetPassword(u);
                          }}
                          className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-all flex items-center justify-center"
                          aria-label="Resetear contraseña"
                          title="Resetear contraseña"
                        >
                          <Key className="h-4 w-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleToggleStatus(u);
                          }}
                          className={`p-2 rounded-lg transition-all flex items-center justify-center ${
                            u.status === 'active'
                              ? 'hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-600 dark:hover:text-red-400'
                              : 'hover:bg-green-50 dark:hover:bg-green-900/20 text-gray-400 hover:text-green-600 dark:hover:text-green-400'
                          }`}
                          aria-label={
                            u.status === 'active' ? 'Desactivar usuario' : 'Activar usuario'
                          }
                          title={u.status === 'active' ? 'Desactivar usuario' : 'Activar usuario'}
                        >
                          {u.status === 'active' ? (
                            <UserX className="h-4 w-4" />
                          ) : (
                            <UserCheck className="h-4 w-4" />
                          )}
                        </button>
                        <div className="w-px h-4 bg-gray-200 dark:bg-gray-700 mx-0.5" />
                        <button
                          onClick={() => navigate(`/admin/users/${u.id}`)}
                          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-all flex items-center justify-center"
                          aria-label="Ver detalles"
                          title="Ver detalles"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredUsers.length === 0 && (
              <EmptyState
                icon={<Users className="h-16 w-16" />}
                title="No se encontraron usuarios"
                description="No hay usuarios que coincidan con tu búsqueda. Intenta con otros términos."
              />
            )}
          </div>
        )}
      </Card>

      {/* Confirmation Modal */}
      {showConfirmModal && confirmAction && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <div
                    className={`w-12 h-12 rounded-full flex items-center justify-center mr-4 ${
                      confirmAction.type === 'reset'
                        ? 'bg-blue-100 dark:bg-blue-900/30'
                        : confirmAction.user.status === 'active'
                          ? 'bg-red-100 dark:bg-red-900/30'
                          : 'bg-green-100 dark:bg-green-900/30'
                    }`}
                  >
                    {confirmAction.type === 'reset' ? (
                      <Key className={`h-6 w-6 ${'text-blue-600 dark:text-blue-400'}`} />
                    ) : confirmAction.user.status === 'active' ? (
                      <UserX className="h-6 w-6 text-red-600 dark:text-red-400" />
                    ) : (
                      <UserCheck className="h-6 w-6 text-green-600 dark:text-green-400" />
                    )}
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                      {confirmAction.type === 'reset'
                        ? 'Resetear Contraseña'
                        : confirmAction.user.status === 'active'
                          ? 'Desactivar Usuario'
                          : 'Activar Usuario'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                      {confirmAction.user.email}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="mb-6">
                <p className="text-gray-700 dark:text-gray-300">
                  {confirmAction.type === 'reset'
                    ? '¿Estás seguro de que deseas resetear la contraseña de este usuario? Se enviará un correo con instrucciones para crear una nueva contraseña.'
                    : confirmAction.user.status === 'active'
                      ? '¿Estás seguro de que deseas desactivar este usuario? El usuario no podrá iniciar sesión hasta que sea reactivado.'
                      : '¿Estás seguro de que deseas activar este usuario? El usuario podrá iniciar sesión nuevamente.'}
                </p>
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  onClick={() => setShowConfirmModal(false)}
                  className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirmAction}
                  className={`px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                    confirmAction.type === 'reset'
                      ? 'bg-blue-600 hover:bg-blue-700'
                      : confirmAction.user.status === 'active'
                        ? 'bg-red-600 hover:bg-red-700'
                        : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {confirmAction.type === 'reset'
                    ? 'Resetear'
                    : confirmAction.user.status === 'active'
                      ? 'Desactivar'
                      : 'Activar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
};

export default UsersListPage;
