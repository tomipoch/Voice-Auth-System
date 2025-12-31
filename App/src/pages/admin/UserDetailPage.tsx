import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import {
  Calendar,
  Shield,
  Mic,
  Activity,
  ArrowLeft,
  CheckCircle,
  XCircle,
  Eye,
  FileText,
  Trash2,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import LoadingSpinner from '../../components/ui/LoadingSpinner'; // Ensure this component exists or import appropriate loading
import adminService, {
  type UserDetails,
  type VerificationAttempt,
} from '../../services/adminService';
import toast from 'react-hot-toast';

// Simple Modal Component (Internal or we could move to ui folder)
const Modal = ({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-md p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <XCircle className="w-6 h-6" />
        </button>
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">{title}</h3>
        {children}
      </div>
    </div>
  );
};

// Interface for phrase result in verification
interface PhraseResult {
  phrase_number: number;
  similarity_score: number;
  asr_confidence: number;
  anti_spoofing_score?: number | null;
  asr_penalty: number;
  final_score: number;
}

// Verification Details Interface
interface VerificationDetails {
  id?: string;
  timestamp?: string;
  metadata?: string;
  results?: PhraseResult[];
  average_score?: number;
  score?: number;
  is_verified?: boolean;
  success?: boolean;
  anti_spoofing_score?: number | null;
  similarity_score?: number;
  device_info?: string;
  ip_address?: string;
  user_agent?: string;
}

// New Modal for Verification Details
const VerificationDetailModal = ({
  details,
  onClose,
}: {
  details: VerificationDetails | string | null;
  onClose: () => void;
}) => {
  if (!details) return null;

  // Parse metadata if it's a string (which it usually is from the DB)
  let parsedMetadata: VerificationDetails;
  if (typeof details === 'string') {
    try {
      parsedMetadata = JSON.parse(details) as VerificationDetails;
    } catch (e) {
      console.error('Error parsing metadata json', e);
      parsedMetadata = {} as VerificationDetails;
    }
  } else if (details.metadata && typeof details.metadata === 'string') {
    try {
      parsedMetadata = JSON.parse(details.metadata) as VerificationDetails;
    } catch (e) {
      console.error('Error parsing metadata json from object', e);
      parsedMetadata = details;
    }
  } else {
    parsedMetadata = details;
  }

  // Normalize data structure
  const results = parsedMetadata.results || [];
  const avgScore = parsedMetadata.average_score || parsedMetadata.score || 0;
  const isVerified = parsedMetadata.is_verified || parsedMetadata.success || false;

  // Safe extraction of top-level anti-spoofing
  const antiSpoofingRaw = parsedMetadata.anti_spoofing_score;
  const antiSpoofingVal =
    antiSpoofingRaw !== undefined && antiSpoofingRaw !== null ? antiSpoofingRaw : null;

  // Calculate Averages for Overview
  const avgSimilarity =
    results.length > 0
      ? results.reduce((acc: number, r: PhraseResult) => acc + (r.similarity_score || 0), 0) /
        results.length
      : parsedMetadata.similarity_score || 0;

  const avgASR =
    results.length > 0
      ? results.reduce((acc: number, r: PhraseResult) => acc + (r.asr_confidence || 0), 0) /
        results.length
      : 1.0; // Default to 1.0 if not available

  // Anti-Spoofing Average Logic (Genuineness)
  // If top level is valid, use it. Else calculate average of phrases.
  let genuinenessScore = 0;
  let hasAntiSpoofing = false;

  if (antiSpoofingVal !== null) {
    genuinenessScore = 1 - antiSpoofingVal;
    hasAntiSpoofing = true;
  } else if (
    results.length > 0 &&
    results.some((r: PhraseResult) => r.anti_spoofing_score != null)
  ) {
    const validSpoofScores = results.filter((r: PhraseResult) => r.anti_spoofing_score != null);
    if (validSpoofScores.length > 0) {
      const avgSpoof =
        validSpoofScores.reduce(
          (acc: number, r: PhraseResult) => acc + (r.anti_spoofing_score || 0),
          0
        ) / validSpoofScores.length;
      genuinenessScore = 1 - avgSpoof;
      hasAntiSpoofing = true;
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-100 dark:border-gray-700 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-100 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 sticky top-0 backdrop-blur-md z-10">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              Detalles de Verificación
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-2">
              <span>
                {parsedMetadata.timestamp
                  ? new Date(parsedMetadata.timestamp).toLocaleString()
                  : 'Fecha no disponible'}
              </span>
              <span className="text-gray-300 dark:text-gray-600">•</span>
              <span className="font-mono text-xs">{parsedMetadata.id || 'ID: --'}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
          >
            <XCircle className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-8">
          {/* 1. Score Overview Section */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Global Score Card */}
            <div
              className={`col-span-1 p-5 rounded-2xl border-2 flex flex-col items-center justify-center text-center
                            ${
                              isVerified
                                ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
                                : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                            }`}
            >
              {isVerified ? (
                <CheckCircle className="w-8 h-8 text-green-600 mb-2" />
              ) : (
                <XCircle className="w-8 h-8 text-red-600 mb-2" />
              )}
              <span
                className={`text-3xl font-bold ${isVerified ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}
              >
                {(avgScore * 100).toFixed(0)}%
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider opacity-70 mt-1">
                {isVerified ? 'Verificación Exitosa' : 'Fallida'}
              </span>
            </div>

            {/* Metrics Grid */}
            <div className="col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
              {/* Similarity Gauge */}
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">
                    Similitud (Voz)
                  </span>
                  <Mic className="w-4 h-4 text-blue-500" />
                </div>
                <div className="flex items-end gap-1 mb-2">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {(avgSimilarity * 100).toFixed(0)}
                  </span>
                  <span className="text-sm text-gray-500 mb-1">%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-blue-500 h-full rounded-full"
                    style={{ width: `${avgSimilarity * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Genuineness Gauge */}
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Genuinidad</span>
                  <Shield
                    className={`w-4 h-4 ${hasAntiSpoofing ? 'text-purple-500' : 'text-gray-400'}`}
                  />
                </div>
                <div className="flex items-end gap-1 mb-2">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {hasAntiSpoofing ? (genuinenessScore * 100).toFixed(1) : '-'}
                  </span>
                  <span className="text-sm text-gray-500 mb-1">%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
                  {hasAntiSpoofing && (
                    <div
                      className={`h-full rounded-full ${genuinenessScore > 0.8 ? 'bg-purple-500' : 'bg-red-500'}`}
                      style={{ width: `${genuinenessScore * 100}%` }}
                    ></div>
                  )}
                </div>
              </div>

              {/* ASR Confidence Gauge */}
              <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-100 dark:border-gray-700">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">
                    Confianza ASR
                  </span>
                  <FileText className="w-4 h-4 text-amber-500" />
                </div>
                <div className="flex items-end gap-1 mb-2">
                  <span className="text-2xl font-bold text-gray-900 dark:text-white">
                    {(avgASR * 100).toFixed(0)}
                  </span>
                  <span className="text-sm text-gray-500 mb-1">%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-amber-500 h-full rounded-full"
                    style={{ width: `${avgASR * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* 2. Detailed Breakdown Table */}
          {results.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-gray-900 dark:text-white uppercase tracking-wide mb-3 flex items-center gap-2">
                <FileText className="w-4 h-4" /> Desglose por Frase
              </h3>
              <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800/80 text-xs text-gray-500 dark:text-gray-400 uppercase font-semibold">
                    <tr>
                      <th className="px-4 py-3 text-left">#</th>
                      <th className="px-4 py-3 text-right text-amber-600 dark:text-amber-500">
                        ASR Conf.
                      </th>
                      <th className="px-4 py-3 text-right text-blue-600 dark:text-blue-500">
                        Similitud
                      </th>
                      <th className="px-4 py-3 text-right text-purple-600 dark:text-purple-500">
                        Genuinidad
                      </th>
                      <th className="px-4 py-3 text-right text-red-600 dark:text-red-500">
                        Penalización
                      </th>
                      <th className="px-4 py-3 text-right bg-gray-100 dark:bg-gray-800">Final</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 dark:divide-gray-800 bg-white dark:bg-gray-900">
                    {results.map((r: PhraseResult, idx: number) => {
                      const phraseGenuineness =
                        r.anti_spoofing_score != null ? 1 - r.anti_spoofing_score : null;
                      return (
                        <tr
                          key={idx}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                        >
                          <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                            Frase {r.phrase_number}
                          </td>
                          <td className="px-4 py-3 text-sm text-right font-mono text-gray-600 dark:text-gray-300">
                            {(r.asr_confidence * 100).toFixed(0)}%
                          </td>
                          <td className="px-4 py-3 text-sm text-right font-mono text-gray-600 dark:text-gray-300">
                            {(r.similarity_score * 100).toFixed(0)}%
                          </td>
                          <td className="px-4 py-3 text-sm text-right font-mono text-gray-600 dark:text-gray-300">
                            {phraseGenuineness !== null
                              ? (phraseGenuineness * 100).toFixed(1) + '%'
                              : '-'}
                          </td>
                          <td className="px-4 py-3 text-sm text-right font-mono">
                            {r.asr_penalty < 1 ? (
                              <span className="bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 px-2 py-0.5 rounded text-xs font-bold">
                                {' '}
                                -{(1 - r.asr_penalty) * 100}%
                              </span>
                            ) : (
                              <span className="text-gray-300">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-right font-mono font-bold text-gray-900 dark:text-white bg-gray-50/50 dark:bg-gray-800/50">
                            {(r.final_score * 100).toFixed(0)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 3. Technical Metadata Footer */}
          <div className="pt-4 border-t border-gray-100 dark:border-gray-700">
            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">
              Detalles Técnicos
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono text-gray-500">
              <div>
                <span className="block text-gray-400 mb-1">Dispositivo</span>
                {parsedMetadata.device_info || 'Desconocido'}
              </div>
              <div>
                <span className="block text-gray-400 mb-1">IP</span>
                {parsedMetadata.ip_address || 'N/A'}
              </div>
              <div className="col-span-2">
                <span className="block text-gray-400 mb-1">User Agent</span>
                <div className="truncate" title={parsedMetadata.user_agent}>
                  {parsedMetadata.user_agent || 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const UserDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState<UserDetails | null>(null);
  const [history, setHistory] = useState<VerificationAttempt[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModelModal, setShowModelModal] = useState(false);
  const [selectedAttempt, setSelectedAttempt] = useState<VerificationAttempt | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [stats, setStats] = useState({
    successRate: 0,
    verificationCount: 0,
    daysActive: 0,
  });

  useEffect(() => {
    if (id) {
      fetchData(id);
    }
  }, [id]);

  const fetchData = async (userId: string) => {
    setLoading(true);
    try {
      const [userData, historyData] = await Promise.all([
        adminService.getUserDetails(userId),
        adminService.getUserHistory(userId),
      ]);

      setUser(userData);

      // Process history
      const attempts = historyData.history.recent_attempts || [];
      setHistory(attempts);

      // Calculate stats
      const totalVerifications = attempts.length;
      const successfulVerifications = attempts.filter((a) => a.result === 'success').length;
      const successRate =
        totalVerifications > 0
          ? Math.round((successfulVerifications / totalVerifications) * 100)
          : 0;

      // Calculate days active (approximate from created_at to now)
      const joinedDate = new Date(userData.created_at);
      const now = new Date();
      const daysActive = Math.floor((now.getTime() - joinedDate.getTime()) / (1000 * 3600 * 24));

      setStats({
        successRate,
        verificationCount: totalVerifications, // Or use historyData.history.total_attempts if available
        daysActive: Math.max(0, daysActive),
      });
    } catch (error) {
      console.error('Error fetching user details:', error);
      toast.error('Error al cargar la información del usuario');
      // Navigate back or show error state? For now, we stay here.
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!user) return;

    try {
      await adminService.deleteUser(user.id);
      toast.success('Usuario eliminado exitosamente');
      navigate('/admin/users');
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('Error al eliminar usuario');
    } finally {
      setShowDeleteModal(false);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex justify-center items-center h-96">
          <LoadingSpinner size="lg" text="Cargando detalles del usuario..." />
        </div>
      </MainLayout>
    );
  }

  if (!user) {
    return (
      <MainLayout>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200">
            Usuario no encontrado
          </h2>
          <Button variant="ghost" onClick={() => navigate('/admin')} className="mt-4">
            Volver al Dashboard
          </Button>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => navigate('/admin/users')}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
            aria-label="Volver a usuarios"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDeleteModal(true)}
            className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20 border-red-300 dark:border-red-800"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Eliminar Usuario
          </Button>
        </div>
        <div>
          <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
            Detalle de Usuario
          </h1>
          <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium">
            Gestionando a {user.first_name} {user.last_name || user.email}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* User Profile Card */}
        <Card className="p-6 bg-linear-to-br from-white to-blue-50/30 dark:from-gray-800 dark:to-blue-900/10 border-blue-100 dark:border-blue-800/30">
          <div className="flex flex-col items-center text-center">
            <div className="relative mb-4">
              <div className="h-20 w-20 rounded-full bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-3xl font-bold shadow-lg">
                {user.first_name
                  ? user.first_name.charAt(0).toUpperCase()
                  : user.email.charAt(0).toUpperCase()}
              </div>
              <div
                className={`absolute -bottom-1 -right-1 w-6 h-6 rounded-full border-2 border-white dark:border-gray-800 ${
                  user.status === 'active' ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-1">
              {user.first_name} {user.last_name}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{user.email}</p>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                user.status === 'active'
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
              }`}
            >
              {user.status === 'active' ? 'Activo' : 'Inactivo'}
            </span>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center text-gray-600 dark:text-gray-300">
                <Shield className="h-4 w-4 mr-2" />
                <span>Rol</span>
              </div>
              <span className="font-medium capitalize">{user.role}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center text-gray-600 dark:text-gray-300">
                <Calendar className="h-4 w-4 mr-2" />
                <span>Registro</span>
              </div>
              <span className="font-medium text-sm">
                {new Date(user.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </Card>

        {/* Biometric Status Card */}
        <Card className="p-6 bg-linear-to-br from-white to-purple-50/30 dark:from-gray-800 dark:to-purple-900/10 border-purple-100 dark:border-purple-800/30">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-6 flex items-center">
            <div className="w-10 h-10 rounded-lg bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mr-3">
              <Mic className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            Estado Biométrico
          </h3>

          <div className="flex flex-col items-center text-center py-6">
            <div
              className={`w-20 h-20 mx-auto rounded-2xl flex items-center justify-center mb-4 shadow-lg ${
                user.enrollment_status === 'enrolled'
                  ? 'bg-linear-to-br from-green-400 to-emerald-600'
                  : 'bg-linear-to-br from-orange-400 to-amber-600'
              }`}
            >
              <Mic className="h-10 w-10 text-white" />
            </div>
            <p className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">
              {user.enrollment_status === 'enrolled' ? 'Voz Registrada' : 'No Registrado'}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-6">
              {user.enrollment_status === 'enrolled'
                ? 'Perfil biométrico activo y listo'
                : 'Usuario pendiente de enrolamiento'}
            </p>

            {user.enrollment_status === 'enrolled' && (
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => setShowModelModal(true)}
              >
                Ver Detalles del Modelo
              </Button>
            )}
          </div>
        </Card>

        {/* Stats Card */}
        <Card className="p-6 bg-linear-to-br from-white to-indigo-50/30 dark:from-gray-800 dark:to-indigo-900/10 border-indigo-100 dark:border-indigo-800/30">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-6 flex items-center">
            <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center mr-3">
              <Activity className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            Métricas de Verificación
          </h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-end mb-3">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Tasa de Éxito
                </span>
                <span
                  className={`text-3xl font-bold ${
                    stats.successRate >= 80
                      ? 'text-green-600 dark:text-green-400'
                      : stats.successRate >= 50
                        ? 'text-yellow-600 dark:text-yellow-400'
                        : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {stats.successRate}%
                </span>
              </div>
              <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-3 overflow-hidden shadow-inner">
                <div
                  className={`h-full rounded-full transition-all duration-500 ease-out ${
                    stats.successRate >= 80
                      ? 'bg-linear-to-r from-green-500 to-emerald-600'
                      : stats.successRate >= 50
                        ? 'bg-linear-to-r from-yellow-500 to-amber-600'
                        : 'bg-linear-to-r from-red-500 to-rose-600'
                  }`}
                  style={{ width: `${stats.successRate}%` }}
                ></div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-linear-to-br from-blue-50 to-blue-100/50 dark:from-blue-900/20 dark:to-blue-800/10 p-4 rounded-xl border border-blue-200 dark:border-blue-800/30">
                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  {stats.verificationCount}
                </p>
                <p className="text-xs font-semibold text-blue-600/70 dark:text-blue-400/70 uppercase tracking-wide">
                  Intentos
                </p>
              </div>
              <div className="bg-linear-to-br from-purple-50 to-purple-100/50 dark:from-purple-900/20 dark:to-purple-800/10 p-4 rounded-xl border border-purple-200 dark:border-purple-800/30">
                <p className="text-3xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                  {stats.daysActive}
                </p>
                <p className="text-xs font-semibold text-purple-600/70 dark:text-purple-400/70 uppercase tracking-wide">
                  Días
                </p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* History Table */}
      <Card className="p-6">
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          Historial de Verificaciones
        </h3>

        {history.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No hay historial de verificaciones reciente.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Fecha
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Método
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Resultado
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                    Score
                  </th>
                  <th className="py-3 px-4"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {history.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors group"
                  >
                    <td className="py-3 px-4 text-gray-900 dark:text-gray-100 text-sm font-medium">
                      {item.date}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-300 text-sm">
                      {item.method || 'Biometría de Voz'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${
                          item.result === 'success'
                            ? 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800/30'
                            : 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-800/30'
                        }`}
                      >
                        {item.result === 'success' ? (
                          <CheckCircle className="w-3.5 h-3.5 mr-1.5" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 mr-1.5" />
                        )}
                        {item.result === 'success' ? 'Exitoso' : 'Fallido'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-2">
                        <span
                          className={`font-mono font-bold w-12 text-right ${
                            item.score >= 80
                              ? 'text-green-600'
                              : item.score >= 50
                                ? 'text-yellow-600'
                                : 'text-red-600'
                          }`}
                        >
                          {item.score}%
                        </span>
                        <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                          <div
                            className={`h-1.5 rounded-full ${
                              item.score >= 80
                                ? 'bg-green-500'
                                : item.score >= 50
                                  ? 'bg-yellow-500'
                                  : 'bg-red-500'
                            }`}
                            style={{ width: `${item.score}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
                        onClick={() => {
                          setSelectedAttempt(item);
                          setShowDetailModal(true);
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Verification Detail Modal */}
      {showDetailModal && selectedAttempt && (
        <VerificationDetailModal
          details={selectedAttempt.details ? JSON.stringify(selectedAttempt.details) : null}
          onClose={() => setShowDetailModal(false)}
        />
      )}
      <Modal
        isOpen={showModelModal}
        onClose={() => setShowModelModal(false)}
        title="Detalles del Modelo Biométrico"
      >
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">ID del Modelo</p>
            <p className="font-mono text-sm break-all font-medium text-gray-900 dark:text-gray-100">
              {user?.voice_template?.id || 'N/A'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Tipo</p>
              <p className="font-medium text-gray-900 dark:text-gray-100">
                {user?.voice_template?.model_type || 'ECAPA-TDNN'}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Muestras</p>
              <p className="font-medium text-gray-900 dark:text-gray-100">
                {user?.voice_template?.sample_count || 1}
              </p>
            </div>
          </div>

          <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Fecha de Creación</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">
              {user?.voice_template?.created_at
                ? new Date(user.voice_template.created_at).toLocaleString()
                : 'Desconocida'}
            </p>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Eliminar Usuario"
      >
        <div className="space-y-4">
          <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800/30">
            <p className="text-sm text-red-800 dark:text-red-300 font-medium">
              ⚠️ Esta acción no se puede deshacer
            </p>
          </div>
          <p className="text-gray-700 dark:text-gray-300">
            ¿Estás seguro de que deseas eliminar a{' '}
            <span className="font-semibold">
              {user?.first_name} {user?.last_name}
            </span>
            ?
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Se eliminarán todos los datos asociados, incluyendo su perfil biométrico y historial de
            verificaciones.
          </p>
          <div className="flex gap-3 justify-end pt-4">
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              Cancelar
            </Button>
            <Button
              variant="primary"
              onClick={handleDeleteUser}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              Eliminar Usuario
            </Button>
          </div>
        </div>
      </Modal>
    </MainLayout>
  );
};

export default UserDetailPage;
