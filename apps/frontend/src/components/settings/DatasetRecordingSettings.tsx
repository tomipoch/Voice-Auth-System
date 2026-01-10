/**
 * Dataset Recording Settings Component
 * Allows superadmin to control dataset audio recording
 */

import { useState, useEffect, useCallback } from 'react';
import { Database, PlayCircle, StopCircle, Users, Mic, Check, RefreshCw } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import Input from '../ui/Input';
import { datasetRecordingService, RecordingStatus } from '../../services/datasetRecordingService';
import toast from 'react-hot-toast';

interface DatasetRecordingSettingsProps {
  className?: string;
}

export default function DatasetRecordingSettings({
  className = '',
}: DatasetRecordingSettingsProps) {
  const [status, setStatus] = useState<RecordingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [sessionName, setSessionName] = useState('dataset_session');

  const fetchStatus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await datasetRecordingService.getStatus();
      setStatus(data);
    } catch (error) {
      console.error('Failed to fetch recording status:', error);
      toast.error('Error al obtener estado de grabación');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    // Poll every 5 seconds when recording is active
    const interval = setInterval(() => {
      if (status?.enabled) {
        fetchStatus();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus, status?.enabled]);

  const handleStart = async () => {
    if (!sessionName.trim()) {
      toast.error('Ingrese un nombre para la sesión');
      return;
    }
    try {
      setActionLoading(true);
      const result = await datasetRecordingService.startRecording(sessionName);
      toast.success(result.message);
      await fetchStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al iniciar grabación');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setActionLoading(true);
      const result = await datasetRecordingService.stopRecording();
      toast.success(result.message);
      await fetchStatus();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al detener grabación');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !status) {
    return (
      <Card className={className}>
        <div className="flex items-center justify-center p-8">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <div className="flex items-center gap-3 mb-4">
        <div
          className={`p-2 rounded-lg ${status?.enabled ? 'bg-green-100 dark:bg-green-900/30' : 'bg-gray-100 dark:bg-gray-700'}`}
        >
          <Database
            className={`w-5 h-5 ${status?.enabled ? 'text-green-600' : 'text-gray-600 dark:text-gray-400'}`}
          />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">Dataset Recording</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Guardar audios de enrollment y verificación
          </p>
        </div>
        {status?.enabled && (
          <span className="ml-auto px-2 py-1 text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full flex items-center gap-1">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            Grabando
          </span>
        )}
      </div>

      {/* Status Panel */}
      {status?.enabled ? (
        <div className="space-y-4">
          {/* Current Session Info */}
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 mb-2">
              <Check className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-green-700 dark:text-green-400">
                Sesión activa: {status.session_id}
              </span>
            </div>
            <p className="text-xs text-green-600 dark:text-green-500 mb-3">{status.session_dir}</p>

            {/* Statistics */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2">
                <div className="flex items-center justify-center gap-1 text-gray-600 dark:text-gray-400 mb-1">
                  <Users className="w-4 h-4" />
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {status.total_users}
                </span>
                <p className="text-xs text-gray-500">Usuarios</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2">
                <div className="flex items-center justify-center gap-1 text-gray-600 dark:text-gray-400 mb-1">
                  <Mic className="w-4 h-4" />
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {status.total_enrollment_audios}
                </span>
                <p className="text-xs text-gray-500">Enrollment</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg p-2">
                <div className="flex items-center justify-center gap-1 text-gray-600 dark:text-gray-400 mb-1">
                  <Check className="w-4 h-4" />
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {status.total_verification_audios}
                </span>
                <p className="text-xs text-gray-500">Verification</p>
              </div>
            </div>
          </div>

          {/* Stop Button */}
          <Button
            variant="danger"
            onClick={handleStop}
            disabled={actionLoading}
            loading={actionLoading}
            className="w-full"
          >
            {!actionLoading && <StopCircle className="w-5 h-5 mr-2" />}
            Detener Grabación
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Session Name Input */}
          <div>
            <Input
              label="Nombre de la sesión"
              value={sessionName}
              onChange={(e) => setSessionName(e.target.value)}
              placeholder="dataset_session"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Los audios se guardarán en: evaluation/dataset/recordings/[nombre]_[timestamp]/
            </p>
          </div>

          {/* Start Button */}
          <Button
            variant="primary"
            onClick={handleStart}
            disabled={actionLoading}
            loading={actionLoading}
            className="w-full"
          >
            {!actionLoading && <PlayCircle className="w-5 h-5 mr-2" />}
            Iniciar Grabación
          </Button>
        </div>
      )}

      {/* Info Footer */}
      <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
        Cuando está activo, todos los audios de enrollment y verificación se guardan automáticamente
        para evaluación.
      </p>
    </Card>
  );
}
