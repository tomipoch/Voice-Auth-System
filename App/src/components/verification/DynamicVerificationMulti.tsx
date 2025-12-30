/**
 * DynamicVerificationMulti Component
 * Verificación con 3 frases dinámicas y cálculo de score promedio
 */

import { useState, useEffect } from 'react';
import { Shield, CheckCircle, XCircle, Loader2, RefreshCw, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import verificationService, {
  type StartMultiPhraseVerificationResponse,
  type VerifyPhraseResponse,
  type Challenge,
  type PhraseResult,
} from '../../services/verificationService';
import { type AudioQuality } from '../../hooks/useAdvancedAudioRecording';
import EnhancedAudioRecorder from '../enrollment/EnhancedAudioRecorder';
import Button from '../ui/Button';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';
import { CountdownTimer } from '../CountdownTimer';

interface DynamicVerificationMultiProps {
  userId: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  onVerificationSuccess: (result: VerifyPhraseResponse) => void;
  onVerificationFailed: (result: VerifyPhraseResponse) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
  className?: string;
}

interface VerificationStep {
  id: string;
  name: string;
  challenge: Challenge;
  audioBlob?: Blob;
  result?: VerifyPhraseResponse;
  completed: boolean;
}

type VerificationPhase =
  | 'initializing'
  | 'ready'
  | 'recording'
  | 'processing'
  | 'completed'
  | 'rejected'
  | 'error';

const DynamicVerificationMulti = ({
  userId,
  difficulty = 'medium',
  onVerificationSuccess,
  onVerificationFailed,
  onError,
  onCancel,
  className,
}: DynamicVerificationMultiProps) => {
  const [phase, setPhase] = useState<VerificationPhase>('initializing');
  const [verificationData, setVerificationData] =
    useState<StartMultiPhraseVerificationResponse | null>(null);
  const [steps, setSteps] = useState<VerificationStep[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [finalResult, setFinalResult] = useState<VerifyPhraseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize multi-phrase verification
  useEffect(() => {
    let isMounted = true;

    const initializeVerification = async () => {
      try {
        setPhase('initializing');
        const response = await verificationService.startMultiPhraseVerification({
          user_id: userId,
          difficulty,
        });

        if (!isMounted) return;

        setVerificationData(response);

        // Create steps based on challenges
        const verificationSteps: VerificationStep[] = response.challenges.map(
          (challenge, index) => ({
            id: `step-${index}`,
            name: `Frase ${index + 1}`,
            challenge,
            completed: false,
          })
        );

        setSteps(verificationSteps);
        setPhase('ready');
      } catch (err) {
        if (!isMounted) return;
        const errorMessage =
          err instanceof Error ? err.message : 'Error al iniciar verificación multi-frase';
        setError(errorMessage);
        setPhase('error');
        onError?.(errorMessage);
      }
    };

    initializeVerification();

    return () => {
      isMounted = false;
    };
  }, [userId, difficulty, onError]);

  // Handle recording complete
  const handleRecordingComplete = async (audioBlob: Blob, quality: AudioQuality) => {
    if (!verificationData || !steps[currentStepIndex]?.challenge) {
      setError('Datos de verificación no disponibles');
      return;
    }

    // Validar duración mínima del lado del cliente
    if (quality.duration < 2.0) {
      setError(
        `Audio demasiado corto (${quality.duration.toFixed(1)}s). Mínimo requerido: 2 segundos`
      );
      setPhase('recording');
      toast.error('Por favor graba por al menos 2 segundos');
      return;
    }

    setPhase('processing');
    setError(null);

    try {
      const currentChallenge = steps[currentStepIndex].challenge;

      // Verify phrase
      const result = await verificationService.verifyPhrase({
        verification_id: verificationData.verification_id,
        challenge_id: currentChallenge.challenge_id,
        phrase_number: currentStepIndex + 1,
        audioBlob,
      });

      // Check if rejected due to spoof
      if (result.rejected) {
        setFinalResult(result);
        setPhase('rejected');
        onVerificationFailed(result);
        return;
      }

      // Update step as completed
      const updatedSteps = [...steps];
      const stepToUpdate = updatedSteps[currentStepIndex];

      if (stepToUpdate) {
        updatedSteps[currentStepIndex] = {
          ...stepToUpdate,
          audioBlob,
          result,
          completed: true,
        };
        setSteps(updatedSteps);
      }

      // Check if verification is complete
      if (result.is_complete) {
        setFinalResult(result);
        setPhase('completed');

        if (result.is_verified) {
          onVerificationSuccess(result);
        } else {
          onVerificationFailed(result);
        }
      } else {
        // Move to next phrase
        setCurrentStepIndex(currentStepIndex + 1);
        setPhase('ready');
      }
    } catch (err: unknown) {
      console.error('Error during verification:', err);

      // Extraer mensaje específico del backend
      let errorMessage = 'Error al verificar frase';

      // Type guard for axios-like error
      const axiosError = err as {
        response?: { status?: number; data?: { message?: string; detail?: string } };
      };

      if (axiosError.response?.status === 400) {
        // Error de validación (ej: audio demasiado corto, mala calidad)
        errorMessage =
          axiosError.response?.data?.message ||
          axiosError.response?.data?.detail ||
          'El audio no cumple con los requisitos de calidad';
      } else if (axiosError.response?.status === 404) {
        errorMessage = 'Sesión de verificación no encontrada';
      } else if (axiosError.response?.status === 500) {
        errorMessage = 'Error del servidor. Por favor, intenta más tarde';
      } else if (!axiosError.response) {
        errorMessage = 'Error de conexión. Verifica tu conexión a internet';
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      setPhase('recording');
      toast.error(errorMessage);
      onError?.(errorMessage);
    }
  };

  // Retry verification
  const handleRetry = () => {
    setSteps([]);
    setCurrentStepIndex(0);
    setFinalResult(null);
    setError(null);
    setPhase('initializing');
  };

  // Get confidence color
  const getConfidenceColor = (score: number) => {
    if (score >= 0.85) return 'text-green-600 dark:text-green-400';
    if (score >= 0.75) return 'text-blue-600 dark:text-blue-400';
    if (score >= 0.65) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  // Render initializing
  if (phase === 'initializing') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Iniciando Verificación
          </h3>
          <p className="text-gray-700 dark:text-gray-300">Obteniendo 3 frases de verificación...</p>
        </div>
      </Card>
    );
  }

  // Render error
  if (phase === 'error') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <XCircle className="w-12 h-12 mx-auto mb-4 text-red-600" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Error en Verificación
          </h3>
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <div className="flex justify-center gap-3">
            {onCancel && (
              <Button onClick={onCancel} variant="ghost">
                Cancelar
              </Button>
            )}
            <Button onClick={handleRetry}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Reintentar
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  // Render rejected (spoof detected)
  if (phase === 'rejected' && finalResult) {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 mx-auto mb-4 text-red-600" />
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Verificación Rechazada
          </h3>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            Se detectó un posible ataque de suplantación
          </p>

          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 mb-4">
            <p className="text-sm text-red-800 dark:text-red-300">
              Razón:{' '}
              {finalResult.reason === 'spoof_detected'
                ? 'Audio falsificado detectado'
                : finalResult.reason}
            </p>
            {finalResult.anti_spoofing_score && (
              <p className="text-sm text-red-800 dark:text-red-300 mt-2">
                Score anti-spoofing: {(finalResult.anti_spoofing_score * 100).toFixed(1)}%
              </p>
            )}
          </div>

          {onCancel && (
            <Button onClick={onCancel} variant="ghost" className="mt-4">
              Volver al inicio
            </Button>
          )}
        </div>
      </Card>
    );
  }

  // Render completed
  if (phase === 'completed' && finalResult) {
    const isSuccess = finalResult.is_verified;

    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          {isSuccess ? (
            <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-600" />
          ) : (
            <XCircle className="w-16 h-16 mx-auto mb-4 text-red-600" />
          )}

          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            {isSuccess ? '¡Verificación Exitosa!' : 'Verificación Fallida'}
          </h3>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            {isSuccess ? 'Tu identidad ha sido confirmada' : 'No se pudo verificar tu identidad'}
          </p>

          <div
            className={`${
              isSuccess ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'
            } rounded-lg p-4 mb-4`}
          >
            <div className="text-center mb-4">
              <p className="text-sm text-gray-600 dark:text-gray-300">Score Promedio Final</p>
              <p
                className={`text-3xl font-bold ${getConfidenceColor(finalResult.average_score || 0)}`}
              >
                {((finalResult.average_score || 0) * 100).toFixed(1)}%
              </p>
            </div>

            {finalResult.all_results && (
              <div className="space-y-2">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Resultados por frase:
                </p>
                {finalResult.all_results.map((phraseResult: PhraseResult) => (
                  <div
                    key={phraseResult.phrase_number}
                    className="flex justify-between items-center text-sm"
                  >
                    <span className="text-gray-700 dark:text-gray-300">
                      Frase {phraseResult.phrase_number}:
                    </span>
                    <span className={getConfidenceColor(phraseResult.final_score)}>
                      {(phraseResult.final_score * 100).toFixed(1)}%
                      {phraseResult.asr_penalty < 1 && ' (penalizado)'}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {finalResult.threshold_used && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs text-gray-600 dark:text-gray-300">
                  Umbral requerido: {(finalResult.threshold_used * 100).toFixed(1)}%
                </p>
              </div>
            )}
          </div>

          {!isSuccess && (
            <div className="flex justify-center gap-3 mt-4">
              {onCancel && (
                <Button onClick={onCancel} variant="ghost">
                  Cancelar
                </Button>
              )}
              <Button onClick={handleRetry} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Intentar Nuevamente
              </Button>
            </div>
          )}
        </div>
      </Card>
    );
  }

  // Render main flow (ready/recording/processing)
  const currentStep = steps[currentStepIndex];
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  return (
    <div className={className}>
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Progreso de Verificación
          </span>
          <span className="text-sm font-medium text-green-600 dark:text-green-400">
            {currentStepIndex + 1} de {steps.length}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className="bg-green-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Educational Info Box */}
      <div className="mb-6 bg-green-50/50 dark:bg-green-900/20 border border-green-200/50 dark:border-green-800/50 rounded-xl p-4">
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          <strong>🔍 ¿Qué estamos haciendo?</strong> Comparamos tu voz con tu perfil biométrico
          registrado para confirmar tu identidad. Lee cada frase con tu voz natural.
        </p>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mt-2">
          <strong>🔒 Seguridad:</strong> Las frases cambian cada vez para evitar que alguien use una
          grabación de tu voz. Solo tú, hablando en tiempo real, puedes pasar la verificación.
        </p>
      </div>

      {/* Current Step Card */}
      <Card className="p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {currentStep?.name}
            </h3>
            <div className="flex items-center gap-4">
              {currentStep?.challenge?.expires_at && (
                <CountdownTimer
                  expiresAt={currentStep.challenge.expires_at}
                  onExpire={handleRetry}
                />
              )}
              <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>

          {/* Audio Recorder */}
          <EnhancedAudioRecorder
            key={currentStepIndex}
            phraseText={currentStep?.challenge?.phrase || ''}
            onRecordingComplete={handleRecordingComplete}
            maxDuration={40}
            minDuration={2}
          />

          {/* Status Messages */}
          {phase === 'processing' && (
            <div className="mt-4">
              <StatusIndicator
                status="loading"
                message={`Verificando frase ${currentStepIndex + 1}...`}
              />
            </div>
          )}

          {error && (
            <div className="mt-4">
              <StatusIndicator status="error" message={error} />
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 mb-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            Consejos para una verificación exitosa:
          </h4>
          <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
            <li>• Asegúrate de estar en un lugar tranquilo</li>
            <li>• Habla con tu voz natural y clara</li>
            <li>• Mantén la misma distancia al micrófono que en el enrollment</li>
            <li>• Lee la frase completa sin pausas largas</li>
          </ul>
        </div>

        {/* Cancel Button */}
        {onCancel && (
          <div className="flex justify-center mt-2">
            <Button
              onClick={onCancel}
              variant="ghost"
              size="sm"
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Cancelar Verificación
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default DynamicVerificationMulti;
