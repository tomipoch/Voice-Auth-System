import { useState, useEffect } from 'react';
import {
  Key,
  Plus,
  Trash2,
  RefreshCw,
  Loader2,
  Copy,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Shield,
  Search,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Input from '../../components/ui/Input';
import toast from 'react-hot-toast';

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  company: string;
  created_at: string;
  last_used?: string;
  is_active: boolean;
  scopes: string[];
}

const ApiKeysPage = () => {
  const [loading, setLoading] = useState(true);
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [showNewKeyModal, setShowNewKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyCompany, setNewKeyCompany] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    setLoading(true);
    try {
      const { superadminService } = await import('../../services/superadminService');
      const keys = await superadminService.getApiKeys();
      setApiKeys(
        keys.map((k) => ({
          id: k.id,
          name: k.name,
          key_prefix: k.key_prefix,
          company: k.company,
          created_at: k.created_at,
          last_used: k.last_used,
          is_active: k.is_active,
          scopes: k.scopes,
        }))
      );
    } catch (error) {
      console.error('Error loading API keys:', error);
      toast.error('Error al cargar claves API');
    } finally {
      setLoading(false);
    }
  };

  // Filtered keys based on search
  const filteredKeys = apiKeys.filter(
    (key) =>
      key.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      key.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      toast.error('El nombre es requerido');
      return;
    }

    try {
      const { superadminService } = await import('../../services/superadminService');
      const result = await superadminService.createApiKey({
        name: newKeyName,
        company: newKeyCompany || 'sistema',
        scopes: ['verify', 'enroll'],
      });

      setGeneratedKey(result.api_key.key);

      // Reload keys to get fresh data
      await loadApiKeys();
      toast.success('Clave API creada exitosamente');
    } catch (error) {
      console.error('Error creating API key:', error);
      toast.error('Error al crear clave API');
    }
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast.success('Clave copiada al portapapeles');
  };

  const handleToggleKey = async (id: string) => {
    try {
      const { superadminService } = await import('../../services/superadminService');
      const result = await superadminService.toggleApiKey(id);
      setApiKeys((keys) =>
        keys.map((k) => (k.id === id ? { ...k, is_active: result.is_active } : k))
      );
      toast.success(result.message);
    } catch (error) {
      console.error('Error toggling API key:', error);
      toast.error('Error al cambiar estado de clave');
    }
  };

  const handleDeleteKey = async (id: string) => {
    if (!confirm('¿Estás seguro de eliminar esta clave API?')) return;
    try {
      const { superadminService } = await import('../../services/superadminService');
      await superadminService.revokeApiKey(id);
      setApiKeys((keys) => keys.filter((k) => k.id !== id));
      toast.success('Clave API eliminada');
    } catch (error) {
      console.error('Error deleting API key:', error);
      toast.error('Error al eliminar clave API');
    }
  };

  const closeModal = () => {
    setShowNewKeyModal(false);
    setNewKeyName('');
    setNewKeyCompany('');
    setGeneratedKey(null);
    setShowKey(false);
  };

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Gestión de API Keys
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
          Administra las claves de acceso a la API
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Total Keys</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">{apiKeys.length}</p>
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
                {apiKeys.filter((k) => k.is_active).length}
              </p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase">Inactivas</p>
              <p className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {apiKeys.filter((k) => !k.is_active).length}
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
              placeholder="Buscar por nombre de API Key..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          </div>
          <div className="flex gap-2 ml-auto">
            <Button variant="secondary" onClick={loadApiKeys} className="h-12">
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button onClick={() => setShowNewKeyModal(true)} className="h-12">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>

      {/* API Keys Table */}
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
                    Nombre
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Clave
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Empresa
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Scopes
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Estado
                  </th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Último Uso
                  </th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-gray-500 uppercase">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {filteredKeys.map((key) => (
                  <tr key={key.id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <Key className="h-4 w-4 text-indigo-500" />
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {key.name}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <code className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm">
                        {key.key_prefix}
                      </code>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-300">
                      {key.company}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex gap-1 flex-wrap">
                        {key.scopes.map((scope, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400"
                          >
                            {scope}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => handleToggleKey(key.id)}
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                          key.is_active
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        {key.is_active ? (
                          <>
                            <CheckCircle className="h-3 w-3 mr-1" /> Activa
                          </>
                        ) : (
                          <>
                            <AlertCircle className="h-3 w-3 mr-1" /> Inactiva
                          </>
                        )}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Nunca'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteKey(key.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {apiKeys.length === 0 && (
              <div className="text-center py-12 text-gray-500">No hay claves API configuradas</div>
            )}
          </div>
        )}
      </Card>

      {/* New Key Modal */}
      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 w-full max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-900/30">
                <Shield className="h-5 w-5 text-indigo-600" />
              </div>
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {generatedKey ? 'Clave API Generada' : 'Nueva Clave API'}
              </h3>
            </div>

            {generatedKey ? (
              <div className="space-y-4">
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-700">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200 mb-2">
                    ⚠️ Guarda esta clave ahora. No podrás verla de nuevo.
                  </p>
                </div>

                <div className="relative">
                  <input
                    type={showKey ? 'text' : 'password'}
                    value={generatedKey}
                    readOnly
                    className="w-full px-4 py-3 pr-20 bg-gray-100 dark:bg-gray-700 rounded-lg font-mono text-sm"
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-1">
                    <button
                      onClick={() => setShowKey(!showKey)}
                      className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                    >
                      {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                    <button
                      onClick={() => handleCopyKey(generatedKey)}
                      className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                    >
                      <Copy className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <Button onClick={closeModal} className="w-full">
                  Entendido
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <Input
                  label="Nombre de la clave"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="Ej: Production API"
                />

                <Input
                  label="Empresa (opcional)"
                  value={newKeyCompany}
                  onChange={(e) => setNewKeyCompany(e.target.value)}
                  placeholder="Ej: Example Corp"
                />

                <div className="flex gap-3">
                  <Button variant="ghost" onClick={closeModal} className="flex-1">
                    Cancelar
                  </Button>
                  <Button onClick={handleCreateKey} className="flex-1">
                    Generar Clave
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </MainLayout>
  );
};

export default ApiKeysPage;
