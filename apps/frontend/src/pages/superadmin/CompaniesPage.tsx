import { useState, useEffect } from 'react';
import {
  Building2,
  Plus,
  Search,
  RefreshCw,
  Loader2,
  CheckCircle,
  XCircle,
  Edit,
  Trash2,
  Users,
  Shield,
  AlertTriangle,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import Select from '../../components/ui/Select';
import { superadminService } from '../../services/superadminService';
import type { CompanyStats } from '../../services/superadminService';
import toast from 'react-hot-toast';

interface Company extends CompanyStats {
  id?: string;
  max_users?: number;
  max_verifications_month?: number;
  created_at?: string;
}

const CompaniesPage = () => {
  const [loading, setLoading] = useState(true);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    max_users: 100,
    max_verifications_month: 10000,
    status: 'active' as 'active' | 'inactive',
  });

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    setLoading(true);
    try {
      const data = await superadminService.getCompanies();
      // Add mock limits for now
      setCompanies(
        data.map((c, i) => ({
          ...c,
          id: `company-${i}`,
          max_users: 100,
          max_verifications_month: 10000,
          created_at: new Date(Date.now() - i * 30 * 24 * 60 * 60 * 1000).toISOString(),
        }))
      );
    } catch (error) {
      console.error('Error loading companies:', error);
      toast.error('Error al cargar empresas');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingCompany(null);
    setFormData({
      name: '',
      max_users: 100,
      max_verifications_month: 10000,
      status: 'active',
    });
    setShowModal(true);
  };

  const handleEdit = (company: Company) => {
    setEditingCompany(company);
    setFormData({
      name: company.name,
      max_users: company.max_users || 100,
      max_verifications_month: company.max_verifications_month || 10000,
      status: company.status,
    });
    setShowModal(true);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      const { superadminService } = await import('../../services/superadminService');

      if (editingCompany) {
        // Update
        await superadminService.updateCompany(editingCompany.name, {
          name: formData.name,
          max_users: formData.max_users,
          max_verifications_month: formData.max_verifications_month,
          status: formData.status,
        });
        setCompanies((prev) =>
          prev.map((c) => (c.id === editingCompany.id ? { ...c, ...formData } : c))
        );
        toast.success('Empresa actualizada');
      } else {
        // Create
        await superadminService.createCompany({
          name: formData.name,
          max_users: formData.max_users,
          max_verifications_month: formData.max_verifications_month,
        });
        const newCompany: Company = {
          id: `company-${Date.now()}`,
          name: formData.name,
          user_count: 0,
          enrolled_count: 0,
          admin_count: 0,
          verification_count_30d: 0,
          status: formData.status,
          max_users: formData.max_users,
          max_verifications_month: formData.max_verifications_month,
          created_at: new Date().toISOString(),
        };
        setCompanies((prev) => [newCompany, ...prev]);
        toast.success('Empresa creada');
      }
      setShowModal(false);
    } catch (error) {
      console.error('Error saving company:', error);
      toast.error('Error al guardar empresa');
    }
  };

  const handleToggleStatus = async (company: Company) => {
    const newStatus = company.status === 'active' ? 'inactive' : 'active';
    try {
      const { superadminService } = await import('../../services/superadminService');
      await superadminService.updateCompany(company.name, { status: newStatus });
      setCompanies((prev) =>
        prev.map((c) => (c.id === company.id ? { ...c, status: newStatus } : c))
      );
      toast.success(`Empresa ${newStatus === 'active' ? 'activada' : 'suspendida'}`);
    } catch (error) {
      console.error('Error toggling company status:', error);
      toast.error('Error al cambiar estado');
    }
  };

  const handleDelete = async (company: Company) => {
    if (!confirm(`¿Eliminar la empresa "${company.name}"? Esta acción no se puede deshacer.`)) {
      return;
    }
    try {
      const { superadminService } = await import('../../services/superadminService');
      await superadminService.deleteCompany(company.name);
      setCompanies((prev) => prev.filter((c) => c.id !== company.id));
      toast.success('Empresa eliminada');
    } catch (error) {
      console.error('Error deleting company:', error);
      toast.error('Error al eliminar empresa');
    }
  };

  const filteredCompanies = companies.filter((c) =>
    c.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Gestión de Empresas
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Crear, editar y administrar empresas del sistema
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Total</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {companies.length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-50 dark:bg-green-900/20 text-green-600">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Activas</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {companies.filter((c) => c.status === 'active').length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Total Usuarios</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {companies.reduce((sum, c) => sum + c.user_count, 0)}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 text-orange-600">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Admins</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {companies.reduce((sum, c) => sum + c.admin_count, 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Actions */}
      <Card className="p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1">
            <Input
              placeholder="Buscar empresa..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          </div>
          <div className="flex gap-2 ml-auto">
            <Button variant="secondary" onClick={loadCompanies} className="h-12">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button onClick={handleCreate} className="h-12">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* Table */}
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
                    Empresa
                  </th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Usuarios
                  </th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Límite
                  </th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Admins
                  </th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Verif/Mes
                  </th>
                  <th className="text-center py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Estado
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {filteredCompanies.map((company) => (
                  <tr key={company.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                          <Building2 className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {company.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            Creada:{' '}
                            {company.created_at
                              ? new Date(company.created_at).toLocaleDateString()
                              : '-'}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="font-medium text-gray-900 dark:text-gray-100">
                        {company.user_count}
                      </span>
                      <span className="text-gray-400"> / {company.enrolled_count} enr.</span>
                    </td>
                    <td className="py-3 px-4 text-center text-sm text-gray-600 dark:text-gray-300">
                      {company.max_users}
                    </td>
                    <td className="py-3 px-4 text-center text-sm text-gray-600 dark:text-gray-300">
                      {company.admin_count}
                    </td>
                    <td className="py-3 px-4 text-center text-sm text-gray-600 dark:text-gray-300">
                      {company.verification_count_30d.toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleToggleStatus(company)}
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                          company.status === 'active'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        {company.status === 'active' ? (
                          <>
                            <CheckCircle className="h-3 w-3 mr-1" /> Activa
                          </>
                        ) : (
                          <>
                            <XCircle className="h-3 w-3 mr-1" /> Suspendida
                          </>
                        )}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(company)}
                          className="hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-900/20"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(company)}
                          className="text-red-500 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredCompanies.length === 0 && (
              <div className="text-center py-12 text-gray-500">No se encontraron empresas</div>
            )}
          </div>
        )}
      </Card>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
              {editingCompany ? 'Editar Empresa' : 'Nueva Empresa'}
            </h3>

            <div className="space-y-4">
              <Input
                label="Nombre de la empresa"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Ej: Acme Corp"
              />

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Límite de usuarios"
                  type="number"
                  value={formData.max_users}
                  onChange={(e) => setFormData({ ...formData, max_users: Number(e.target.value) })}
                />
                <Input
                  label="Verif./mes"
                  type="number"
                  value={formData.max_verifications_month}
                  onChange={(e) =>
                    setFormData({ ...formData, max_verifications_month: Number(e.target.value) })
                  }
                />
              </div>

              <Select
                label="Estado"
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value as 'active' | 'inactive' })
                }
              >
                <option value="active">Activa</option>
                <option value="inactive">Suspendida</option>
              </Select>

              <div className="flex gap-3 pt-4">
                <Button variant="ghost" onClick={() => setShowModal(false)} className="flex-1">
                  Cancelar
                </Button>
                <Button onClick={handleSubmit} className="flex-1">
                  {editingCompany ? 'Guardar' : 'Crear'}
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </MainLayout>
  );
};

export default CompaniesPage;
