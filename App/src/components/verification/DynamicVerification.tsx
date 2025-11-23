/**
 * DynamicVerification Component
 * Componente para verificación con frases dinámicas del sistema
 */

import { useState, useEffect } from 'react';
import { Shield, CheckCircle, XCircle, Loader2, RefreshCw, AlertTriangle } from 'lucide-react';
import verificationService, { type StartVerificationResponse, type VerifyVoiceResponse } from '../../services/verificationService';
import AudioRecorder from '../ui/AudioRecorder';
import Button from '../ui/Button';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';

interface DynamicVerificationProps {
  userId: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  maxAttempts?: number;
  onVerificationSuccess: (result: VerifyVoiceResponse) => void;
  onVerificationFailed: (result: VerifyVoiceResponse) => void;
  onError?: (error: string) => void;
  className?: string;
}

type VerificationPhase = 'initializing' | 'ready' | 'recording' | 'processing' | 'success' | 'failed' | 'blocked' | 'error';

const DynamicVerification = ({
  userId,
  difficulty = 'medium',
  maxAttempts = 3,
  onVerificationSuccess,
  onVerificationFailed,
  onError,
  className,
}: DynamicVerificationProps) => {
  const [phase, setPhase] = useState<VerificationPhase>('initializing');
  const [verificationData, setVerificationData] = useState<StartVerificationResponse | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerifyVoiceResponse | null>(null);
  const [currentAttempt, setCurrentAttempt] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Inicializar verificación
  useEffect(() => {
    initializeVerification();
  }, [userId, difficulty]);

  const initializeVerification = async () => {
    try {
      setPhase('initializing');
      setError(null);
      
      const response = await verificationService.startVerification({
        user_id: userId,
        difficulty,
      });

      setVerificationData(response);
      setPhase('ready');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al iniciar verificación';
      setError(errorMessage);
      setPhase('error');
      onError?.(errorMessage);
    }
  };

  // Manejar grabación completada
  const handleRecordingComplete = async (audioBlob: Blob, _quality: any) => {
    if (!verificationData) {
      setError('Datos de verificación no disponibles');
      return;
    }

    setPhase('processing');
    setError(null);

    try {
      const result = await verificationService.verifyVoice({
        verification_id: verificationData.verification_id,
        phrase_id: verificationData.phrase.id,
        audioBlob,
      });

      setVerificationResult(result);

      if (result.is_verified) {
        setPhase('success');
        onVerificationSuccess(result);
      } else {
        const newAttempt = currentAttempt + 1;
        setCurrentAttempt(newAttempt);

        if (newAttempt >= maxAttempts) {
          setPhase('blocked');
        } else {
          setPhase('failed');
        }
        
        onVerificationFailed(result);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al verificar voz';
      setError(errorMessage);
      setPhase('failed');
      setCurrentAttempt(currentAttempt + 1);
      onError?.(errorMessage);
    }
  };

  // Reintentar verificación
  const handleRetry = () => {
    setVerificationResult(null);
    setError(null);
    initializeVerification();
  };

  // Obtener mensaje según el estado
  const getStatusMessage = () => {
    switch (phase) {
      case 'initializing':
        return 'Preparando verificación...';
      case 'ready':
        return 'Lee la frase mostrada de forma clara y natural';
      case 'processing':
        return 'Analizando tu voz...';
      case 'success':
        return '¡Verificación exitosa! Identidad confirmada';
      case 'failed':
        return `Verificación fallida. Intentos restantes: ${maxAttempts - currentAttempt}`;
      case 'blocked':
        return 'Demasiados intentos fallidos. Intenta más tarde.';
      case 'error':
        return error || 'Error en la verificación';
      default:
        return '';
    }
  };

  // Obtener color del confidence score
  const getConfidenceColor = (score: number) => {
    if (score >= 0.85) return 'text-green-600 dark:text-green-400';
    if (score >= 0.75) return 'text-blue-600 dark:text-blue-400';
    if (score >= 0.65) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  // Renderizar según la fase
  if (phase === 'initializing') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Iniciando Verificación
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Obteniendo frase de verificación...
          </p>
        </div>
      </Card>
    );
  }

  if (phase === 'error') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-red-600" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Error en Verificación
          </h3>
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <Button onClick={handleRetry}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Reintentar
          </Button>
        </div>
      </Card>
    );
  }

  if (phase === 'success') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-600" />
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            ¡Verificación Exitosa!
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Tu identidad ha sido confirmada
          </p>

          {verificationResult && (
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 mb-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Confianza</p>
                  <p className={`text-lg font-bold ${getConfidenceColor(verificationResult.confidence_score)}`}>
                    {(verificationResult.confidence_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Similitud</p>
                  <p className={`text-lg font-bold ${getConfidenceColor(verificationResult.similarity_score)}`}>
                    {(verificationResult.similarity_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Voz en vivo</p>
                  <p className="text-lg font-bold text-green-600 dark:text-green-400">
                    {verificationResult.is_live ? '✓ Sí' : '✗ No'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-500 dark:text-gray-400">Frase correcta</p>
                  <p className="text-lg font-bold text-green-600 dark:text-green-400">
                    {verificationResult.phrase_match ? '✓ Sí' : '✗ No'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>
    );
  }

  if (phase === 'blocked') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-600" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Acceso Bloqueado
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Has alcanzado el máximo de intentos fallidos
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Por favor, intenta nuevamente más tarde
          </p>
        </div>
      </Card>
    );
  }

  return (
    <div className={className}>
      <Card className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Verificación de Voz
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Intento {currentAttempt + 1} de {maxAttempts}
            </p>
          </div>
          <Shield className="w-8 h-8 text-blue-600 dark:text-blue-400" />
        </div>

        {/* Phrase Display */}
        {verificationData && (
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center mb-2">
              Lee esta frase:
            </p>
            <p className="text-center text-lg font-medium text-gray-900 dark:text-gray-100">
              "{verificationData.phrase.text}"
            </p>
            <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-2">
              Dificultad: {verificationData.phrase.difficulty}
            </p>
          </div>
        )}

        {/* Audio Recorder */}
        <AudioRecorder
          onRecordingComplete={handleRecordingComplete}
          maxDuration={30}
        />

        {/* Status Messages */}
        <div className="mt-4">
          {phase === 'processing' && (
            <StatusIndicator
              status="loading"
              message={getStatusMessage()}
            />
          )}

          {phase === 'failed' && verificationResult && (
            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
              <div className="flex items-start">
                <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-3" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-800 dark:text-red-300 mb-2">
                    {getStatusMessage()}
                  </p>
                  <div className="text-sm text-red-700 dark:text-red-400">
                    <p>Confianza: {(verificationResult.confidence_score * 100).toFixed(1)}%</p>
                    <p>Umbral requerido: {(verificationResult.threshold_used * 100).toFixed(1)}%</p>
                  </div>
                </div>
              </div>
              {currentAttempt < maxAttempts && (
                <Button
                  onClick={handleRetry}
                  variant="outline"
                  size="sm"
                  className="mt-4"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Intentar con nueva frase
                </Button>
              )}
            </div>
          )}

          {error && (
            <StatusIndicator
              status="error"
              message={error}
            />
          )}
        </div>

        {/* Instructions */}
        {(phase === 'ready' || phase === 'failed') && (
          <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 mt-6">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
              Consejos para una verificación exitosa:
            </h4>
            <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
              <li>• Asegúrate de estar en un lugar tranquilo</li>
              <li>• Habla con tu voz natural y clara</li>
              <li>• Mantén la misma distancia al micrófono que en el enrollment</li>
              <li>• Lee la frase completa sin pausas largas</li>
            </ul>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DynamicVerification;
