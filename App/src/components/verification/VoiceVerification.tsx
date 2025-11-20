import { useState } from 'react';
import { Shield, CheckCircle, XCircle, AlertTriangle, RotateCcw, Clock } from 'lucide-react';
import AudioRecorder from '../ui/AudioRecorder';
import { AudioQuality } from '../../hooks/useAdvancedAudioRecording';
import Button from '../ui/Button';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';

interface VerificationResult {
  success: boolean;
  confidence?: number;
  threshold?: number;
  phrase?: string;
  [key: string]: unknown;
}

interface VoiceVerificationProps {
  challenge: string;
  onVerificationComplete: (audioData: Blob, challenge: string) => Promise<VerificationResult>;
  maxAttempts?: number;
  className?: string;
}

type VerificationState = 'loading' | 'ready' | 'processing' | 'success' | 'failed' | 'blocked';

const VoiceVerification = ({
  challenge,
  onVerificationComplete,
  maxAttempts = 3,
  className,
}: VoiceVerificationProps) => {
  const [currentAttempt, setCurrentAttempt] = useState(0);
  const [verificationState, setVerificationState] = useState<VerificationState>(
    challenge ? 'ready' : 'loading'
  );
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRecordingComplete = async (audioData: Blob, quality: AudioQuality) => {
    if (!quality?.isValid) {
      setError('La calidad del audio es insuficiente. Por favor, graba nuevamente.');
      return;
    }

    setVerificationState('processing');
    setError(null);

    try {
      // Simular proceso de verificación
      const result = await onVerificationComplete(audioData, challenge);
      setVerificationResult(result);

      if (result.success) {
        setVerificationState('success');
      } else {
        setCurrentAttempt((prev) => prev + 1);
        if (currentAttempt + 1 >= maxAttempts) {
          setVerificationState('blocked');
        } else {
          setVerificationState('failed');
        }
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Error durante la verificación';
      setError(errorMessage);
      setVerificationState('failed');
      setCurrentAttempt((prev) => prev + 1);
    }
  };

  const handleRetry = () => {
    setVerificationState('ready');
    setVerificationResult(null);
    setError(null);
  };

  const getVerificationMessage = () => {
    switch (verificationState) {
      case 'ready':
        return 'Lee la frase mostrada de forma natural y clara';
      case 'processing':
        return 'Procesando y verificando tu voz...';
      case 'success':
        return '¡Verificación exitosa! Tu identidad ha sido confirmada';
      case 'failed':
        return `Verificación fallida. Intentos restantes: ${maxAttempts - currentAttempt}`;
      case 'blocked':
        return 'Demasiados intentos fallidos. Intenta nuevamente más tarde.';
      default:
        return '';
    }
  };

  const getStatusIndicator = () => {
    switch (verificationState) {
      case 'processing':
        return <StatusIndicator status="loading" message="Verificando..." />;
      case 'success':
        return <StatusIndicator status="success" message="Verificación exitosa" />;
      case 'failed':
        return <StatusIndicator status="error" message="Verificación fallida" />;
      case 'blocked':
        return <StatusIndicator status="error" message="Acceso bloqueado" />;
      default:
        return null;
    }
  };

  if (!challenge) {
    return (
      <Card className={`p-8 text-center ${className}`}>
        <Clock className="h-16 w-16 text-gray-400 dark:text-blue-400/70 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-200 mb-2">
          Cargando desafío...
        </h3>
        <p className="text-gray-600 dark:text-blue-400/70">
          Espera mientras preparamos tu frase de verificación
        </p>
      </Card>
    );
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div className="text-center mb-6">
        <div
          className={`w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center ${
            verificationState === 'success'
              ? 'bg-green-100 dark:bg-green-900/30'
              : verificationState === 'failed' || verificationState === 'blocked'
                ? 'bg-red-100 dark:bg-red-900/30'
                : verificationState === 'processing'
                  ? 'bg-blue-100 dark:bg-blue-900/30'
                  : 'bg-gray-100 dark:bg-gray-800/70'
          }`}
        >
          {verificationState === 'success' ? (
            <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
          ) : verificationState === 'failed' || verificationState === 'blocked' ? (
            <XCircle className="h-10 w-10 text-red-600 dark:text-red-400" />
          ) : verificationState === 'processing' ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 dark:border-blue-400" />
          ) : (
            <Shield className="h-10 w-10 text-gray-600 dark:text-blue-400/70" />
          )}
        </div>

        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-200 mb-2">
          Verificación por Voz
        </h2>

        <p className="text-gray-600 dark:text-blue-400/70 mb-4">{getVerificationMessage()}</p>

        {getStatusIndicator()}
      </div>

      {/* Frase de desafío */}
      {verificationState === 'ready' && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-700/60 rounded-lg p-6 mb-6">
          <div className="text-center">
            <h3 className="text-sm font-medium text-blue-900 dark:text-blue-300 mb-2">
              Lee la siguiente frase:
            </h3>
            <p className="text-xl font-bold text-blue-900 dark:text-blue-300">"{challenge}"</p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700/60 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 dark:text-red-400 mr-2" />
            <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Grabador de audio */}
      {verificationState === 'ready' && (
        <div className="mb-6">
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            maxDuration={10}
            minDuration={2}
            showQualityAnalysis={true}
            className="border-0 shadow-none bg-transparent p-0"
          />
        </div>
      )}

      {/* Estado de procesamiento */}
      {verificationState === 'processing' && (
        <div className="text-center mb-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700/70 rounded w-3/4 mx-auto mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700/70 rounded w-1/2 mx-auto"></div>
          </div>
          <p className="text-sm text-gray-600 dark:text-blue-400/70 mt-4">
            Esto puede tomar unos segundos...
          </p>
        </div>
      )}

      {/* Resultado de verificación */}
      {verificationResult &&
        (verificationState === 'success' || verificationState === 'failed') && (
          <div
            className={`border rounded-lg p-4 mb-6 ${
              verificationState === 'success'
                ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-700/60'
                : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-700/60'
            }`}
          >
            <h4
              className={`text-sm font-medium mb-2 ${
                verificationState === 'success'
                  ? 'text-green-900 dark:text-green-300'
                  : 'text-red-900 dark:text-red-300'
              }`}
            >
              Resultado de la Verificación
            </h4>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span
                  className={
                    verificationState === 'success'
                      ? 'text-green-700 dark:text-green-400'
                      : 'text-red-700 dark:text-red-400'
                  }
                >
                  Confianza:
                </span>
                <span className="font-medium ml-2">
                  {((verificationResult.confidence || 0) * 100).toFixed(1)}%
                </span>
              </div>
              <div>
                <span
                  className={
                    verificationState === 'success'
                      ? 'text-green-700 dark:text-green-400'
                      : 'text-red-700 dark:text-red-400'
                  }
                >
                  Umbral:
                </span>
                <span className="font-medium ml-2">
                  {((verificationResult.threshold || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        )}

      {/* Controles */}
      <div className="flex justify-center space-x-3">
        {verificationState === 'failed' && currentAttempt < maxAttempts && (
          <Button onClick={handleRetry}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Intentar Nuevamente
          </Button>
        )}

        {verificationState === 'blocked' && (
          <Button variant="secondary" disabled>
            Demasiados intentos
          </Button>
        )}

        {verificationState === 'success' && (
          <div className="text-center">
            <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400 mx-auto mb-2" />
            <p className="text-green-600 dark:text-green-400 font-medium">Acceso concedido</p>
          </div>
        )}
      </div>

      {/* Información de intentos */}
      {maxAttempts > 1 && currentAttempt > 0 && verificationState !== 'success' && (
        <div className="mt-4 text-center text-sm text-gray-600 dark:text-blue-400/70">
          Intento {currentAttempt} de {maxAttempts}
        </div>
      )}
    </Card>
  );
};

export default VoiceVerification;
