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
      // Mock API keys - in production this would call the backend
      setApiKeys([
        {
          id: '1',
          name: 'Production API Key',
          key_prefix: 'vb_prod_****',
          company: 'Example Corp',
          created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          last_used: new Date().toISOString(),
          is_active: true,
          scopes: ['verify', 'enroll'],
        },
        {
          id: '2',
          name: 'Development Key',
          key_prefix: 'vb_dev_****',
          company: 'Familia',
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          is_active: true,
          scopes: ['verify'],
        },
        {
          id: '3',
          name: 'Legacy Integration',
          key_prefix: 'vb_leg_****',
          company: 'sistema',
          created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
          last_used: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          is_active: false,
          scopes: ['verify', 'enroll', 'admin'],
        },
      ]);
    } catch (error) {
      console.error('Error loading API keys:', error);
      toast.error('Error al cargar claves API');
    } finally {
      setLoading(false);
    }
  };

  // Filtered keys based on search
  const filteredKeys = apiKeys.filter((key) =>
    key.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    key.company.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      toast.error('El nombre es requerido');
      return;
    }

    // Mock key generation
    const newKey = `vb_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
    setGeneratedKey(newKey);
    
    const key: ApiKey = {
      id: Date.now().toString(),
      name: newKeyName,
      key_prefix: newKey.substring(0, 10) + '****',
      company: newKeyCompany || 'sistema',
      created_at: new Date().toISOString(),
      is_active: true,
      scopes: ['verify', 'enroll'],
    };
    
    setApiKeys([key, ...apiKeys]);
    toast.success('Clave API creada exitosamente');
  };

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key);
    toast.success('Clave copiada al portapapeles');
  };

  const handleToggleKey = (id: string) => {
    setApiKeys(keys => 
      keys.map(k => k.id === id ? { ...k, is_active: !k.is_active } : k)
    );
    toast.success('Estado de la clave actualizado');
  };

  const handleDeleteKey = (id: string) => {
    if (!confirm('¿Estás seguro de eliminar esta clave API?')) return;
    setApiKeys(keys => keys.filter(k => k.id !== id));
    toast.success('Clave API eliminada');
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
        <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-purple-700 to-indigo-800 dark:from-gray-200 dark:via-purple-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
          Gestión de API Keys
        </h1>
        <p className="text-lg text-purple-600/80 dark:text-purple-400/80 font-medium">
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
                {apiKeys.filter(k => k.is_active).length}
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
                {apiKeys.filter(k => !k.is_active).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Search and Actions */}
      <Card className="p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por nombre de API Key..."
              className="w-full pl-10 pr-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-500/50"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
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
            <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
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
                        <Key className="h-4 w-4 text-purple-500" />
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
                          <><CheckCircle className="h-3 w-3 mr-1" /> Activa</>
                        ) : (
                          <><AlertCircle className="h-3 w-3 mr-1" /> Inactiva</>
                        )}
                      </button>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-500">
                      {key.last_used
                        ? new Date(key.last_used).toLocaleDateString()
                        : 'Nunca'}
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
              <div className="text-center py-12 text-gray-500">
                No hay claves API configuradas
              </div>
            )}
          </div>
        )}
      </Card>

      {/* New Key Modal */}
      {showNewKeyModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="p-6 w-full max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                <Shield className="h-5 w-5 text-purple-600" />
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
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Nombre de la clave
                  </label>
                  <input
                    type="text"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="Ej: Production API"
                    className="w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Empresa (opcional)
                  </label>
                  <input
                    type="text"
                    value={newKeyCompany}
                    onChange={(e) => setNewKeyCompany(e.target.value)}
                    placeholder="Ej: Example Corp"
                    className="w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800"
                  />
                </div>

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
