/**
 * DynamicEnrollment Component
 * Componente para enrollment con frases dinámicas del sistema
 */

import { useState, useEffect } from 'react';
import { Shield, CheckCircle, XCircle, Loader2, RefreshCw, AlertTriangle } from 'lucide-react';
import enrollmentService, {
  type Phrase,
  type StartEnrollmentResponse,
} from '../../services/enrollmentService';
import { type AudioQuality } from '../../hooks/useAdvancedAudioRecording';
import EnhancedAudioRecorder from './EnhancedAudioRecorder';
import Button from '../ui/Button';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';

interface DynamicEnrollmentProps {
  userId?: string;
  externalRef?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
  onEnrollmentComplete: (voiceprintId: string, qualityScore: number) => void;
  onError?: (error: string) => void;
  onCancel?: () => void;
  className?: string;
}

interface EnrollmentStep {
  id: string;
  name: string;
  description: string;
  challenge_id?: string; // Added for backend validation
  phrase?: Phrase;
  audioBlob?: Blob;
  completed: boolean;
}

type EnrollmentPhase = 'idle' | 'initializing' | 'recording' | 'completing' | 'completed' | 'error';

const DynamicEnrollment = ({
  userId,
  externalRef,
  difficulty = 'medium',
  onEnrollmentComplete,
  onError,
  onCancel,
  className,
}: DynamicEnrollmentProps) => {
  const [phase, setPhase] = useState<EnrollmentPhase>('initializing');
  const [enrollmentData, setEnrollmentData] = useState<StartEnrollmentResponse | null>(null);
  const [steps, setSteps] = useState<EnrollmentStep[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showOverwriteModal, setShowOverwriteModal] = useState(false);

  // Inicializar enrollment
  useEffect(() => {
    const initializeEnrollment = async () => {
      try {
        setPhase('initializing');

        const response = await enrollmentService.startEnrollment({
          user_id: userId,
          external_ref: externalRef,
          difficulty,
        });

        // Check if voiceprint exists
        if (response.voiceprint_exists) {
          setShowOverwriteModal(true);
          setPhase('idle');
          return;
        }

        setEnrollmentData(response);

        // Crear pasos basados en las frases (challenges)
        const enrollmentSteps: EnrollmentStep[] = response.challenges.map((challenge, index) => ({
          id: `step-${index}`,
          name: `Frase ${index + 1}`,
          description: challenge.phrase,
          challenge_id: challenge.challenge_id, // Store challenge_id for backend
          phrase: {
            id: challenge.phrase_id,
            text: challenge.phrase,
            difficulty: challenge.difficulty,
            word_count: challenge.phrase.split(' ').length,
          },
          completed: false,
        }));

        setSteps(enrollmentSteps);
        setPhase('recording');
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Error al iniciar enrollment';
        setError(errorMessage);
        setPhase('error');
        onError?.(errorMessage);
      }
    };

    initializeEnrollment();
  }, [userId, externalRef, difficulty, onError]);

  // Handle voiceprint overwrite confirmation
  const handleOverwriteConfirm = async () => {
    try {
      setShowOverwriteModal(false);
      setPhase('initializing');

      const response = await enrollmentService.startEnrollment({
        user_id: userId,
        external_ref: externalRef,
        difficulty,
        force_overwrite: true,
      });

      setEnrollmentData(response);

      const enrollmentSteps: EnrollmentStep[] = response.challenges.map((challenge, index) => ({
        id: `step-${index}`,
        name: `Frase ${index + 1}`,
        description: challenge.phrase,
        challenge_id: challenge.challenge_id,
        phrase: {
          id: challenge.phrase_id,
          text: challenge.phrase,
          difficulty: challenge.difficulty,
          word_count: challenge.phrase.split(' ').length,
        },
        completed: false,
      }));

      setSteps(enrollmentSteps);
      setPhase('recording');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al iniciar enrollment';
      setError(errorMessage);
      setPhase('error');
      onError?.(errorMessage);
    }
  };

  const handleOverwriteCancel = () => {
    setShowOverwriteModal(false);
    onCancel?.();
  };

  // Manejar grabación completada
  const handleRecordingComplete = async (audioBlob: Blob, _quality: AudioQuality) => {
    if (!enrollmentData || !steps[currentStepIndex]?.phrase) {
      setError('Datos de enrollment no disponibles');
      return;
    }

    setIsProcessing(true);

    try {
      const currentStep = steps[currentStepIndex];
      // Recording started successfully

      // Enviar muestra al servidor usando challenge_id
      const response = await enrollmentService.addSample(
        enrollmentData.enrollment_id,
        currentStep.challenge_id!, // Use challenge_id instead of phrase_id
        audioBlob
      );

      // Actualizar paso como completado
      const updatedSteps = [...steps];
      const updatedStep = updatedSteps[currentStepIndex];
      if (updatedStep) {
        updatedSteps[currentStepIndex] = {
          ...updatedStep,
          audioBlob,
          completed: true,
        };
      }
      setSteps(updatedSteps);

      // Si es el último paso, completar enrollment
      if (response.is_complete) {
        await completeEnrollment();
      } else {
        // Avanzar al siguiente paso
        setCurrentStepIndex(currentStepIndex + 1);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al procesar audio';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  // Completar enrollment
  const completeEnrollment = async () => {
    if (!enrollmentData) return;

    setPhase('completing');
    setIsProcessing(true);

    try {
      const response = await enrollmentService.completeEnrollment(enrollmentData.enrollment_id);

      setPhase('completed');
      onEnrollmentComplete(response.voiceprint_id, response.enrollment_quality);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al completar enrollment';
      setError(errorMessage);
      setPhase('error');
      onError?.(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  // Renderizar según la fase
  if (phase === 'initializing') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <Loader2 className="w-12 h-12 mx-auto mb-4 animate-spin text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            Iniciando Enrollment
          </h3>
          <p className="text-gray-700 dark:text-gray-300">Preparando frases dinámicas...</p>
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
            Error en Enrollment
          </h3>
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <div className="flex justify-center gap-3">
            {onCancel && (
              <Button onClick={onCancel} variant="ghost">
                Cancelar
              </Button>
            )}
            <Button onClick={() => window.location.reload()}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Reintentar
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  if (phase === 'completed') {
    return (
      <Card className={`p-8 ${className}`}>
        <div className="text-center">
          <CheckCircle className="w-16 h-16 mx-auto mb-4 text-green-600" />
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            ¡Enrollment Completado!
          </h3>
          <p className="text-gray-700 dark:text-gray-300">
            Tu huella de voz ha sido creada exitosamente
          </p>
        </div>
      </Card>
    );
  }

  const currentStep = steps[currentStepIndex];
  const progress = ((currentStepIndex + 1) / steps.length) * 100;

  return (
    <div className={className}>
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Progreso del Enrollment
          </span>
          <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
            {currentStepIndex + 1} de {steps.length}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Educational Info Box */}
      <div className="mb-6 bg-blue-50/50 dark:bg-blue-900/20 border border-blue-200/50 dark:border-blue-800/50 rounded-xl p-4">
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          <strong>📝 ¿Qué estamos haciendo?</strong> Estamos creando tu huella vocal única
          analizando las características de tu voz (frecuencia, ritmo, entonación). Lee cada frase
          con tu voz natural.
        </p>
        <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mt-2">
          <strong>💡 Frases aleatorias:</strong> Cambian en cada sesión para garantizar seguridad y
          prevenir fraudes con grabaciones.
        </p>
      </div>

      {/* Current Step Card */}
      <Card className="p-6">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              {currentStep?.name}
            </h3>
            <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>

          {/* Enhanced Audio Recorder with Countdown and VAD */}
          <EnhancedAudioRecorder
            key={currentStepIndex} // Force remount when step changes
            phraseText={currentStep?.phrase?.text || ''}
            onRecordingComplete={handleRecordingComplete}
            maxDuration={30}
            minDuration={2}
          />

          {/* Status Messages */}
          {isProcessing && (
            <div className="mt-4">
              <StatusIndicator status="loading" message="Procesando audio..." />
            </div>
          )}

          {error && (
            <div className="mt-4">
              <StatusIndicator status="error" message={error} />
            </div>
          )}

          {phase === 'completing' && (
            <div className="mt-4">
              <StatusIndicator
                status="loading"
                message="Completando enrollment y creando huella de voz..."
              />
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 mb-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
            Consejos para una mejor grabación:
          </h4>
          <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
            <li>• Encuentra un lugar tranquilo sin ruido de fondo</li>
            <li>• Habla con tu voz natural, ni muy alto ni muy bajo</li>
            <li>• Mantén el micrófono a una distancia constante</li>
            <li>• Lee la frase completa de forma fluida</li>
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
              Cancelar Registro
            </Button>
          </div>
        )}
      </Card>

      {/* Voiceprint Overwrite Confirmation Modal */}
      {showOverwriteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <Card className="max-w-md mx-4 p-6">
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-orange-100 dark:bg-orange-900/30 mb-4">
                <AlertTriangle className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>

              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Huella de Voz Existente
              </h3>

              <p className="text-sm text-gray-700 dark:text-gray-300 mb-6">
                Ya tienes una huella de voz registrada. ¿Deseas sobrescribirla con un nuevo
                registro? Esta acción no se puede deshacer.
              </p>

              <div className="flex gap-3 justify-center">
                <Button onClick={handleOverwriteCancel} variant="outline" className="flex-1">
                  Cancelar
                </Button>
                <Button
                  onClick={handleOverwriteConfirm}
                  className="flex-1 bg-orange-600 hover:bg-orange-700 text-white"
                >
                  Sobrescribir
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default DynamicEnrollment;
