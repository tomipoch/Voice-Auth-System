import { Check, Clock, AlertCircle } from 'lucide-react';
import Card from '../ui/Card';
import Button from '../ui/Button';
import StatusIndicator from '../ui/StatusIndicator';

interface Recording {
  isValid: boolean;
  [key: string]: unknown;
}

interface EnrollmentProgressProps {
  recordings: (Recording | null)[];
  totalSteps?: number;
  onSubmit: () => void;
  isSubmitting?: boolean;
  canSubmit?: boolean;
}

const EnrollmentProgress = ({
  recordings,
  totalSteps = 5,
  onSubmit,
  isSubmitting = false,
  canSubmit = false,
}: EnrollmentProgressProps) => {
  const completedSteps = recordings.filter((r) => r && r.isValid).length;
  const progressPercentage = (completedSteps / totalSteps) * 100;

  const getStepStatus = (stepIndex: number): 'pending' | 'completed' | 'error' => {
    const recording = recordings[stepIndex];
    if (!recording) return 'pending';
    return recording.isValid ? 'completed' : 'error';
  };

  const getStepIcon = (status: string): React.ReactElement => {
    switch (status) {
      case 'completed':
        return <Check className="h-4 w-4 text-green-600" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <Card className="p-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Progreso del Registro</h3>
        <p className="text-gray-600">
          {completedSteps} de {totalSteps} pasos completados
        </p>
      </div>

      {/* Barra de progreso */}
      <div className="mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Progreso</span>
          <span>{Math.round(progressPercentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-500"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Lista de pasos */}
      <div className="space-y-3 mb-6">
        {Array.from({ length: totalSteps }, (_, index) => {
          const stepNumber = index + 1;
          const status = getStepStatus(index);
          const recording = recordings[index];

          return (
            <div
              key={stepNumber}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">{getStepIcon(status)}</div>
                <div>
                  <p className="text-sm font-medium text-gray-900">Paso {stepNumber}</p>
                  {recording && (recording as { quality?: string; duration?: number }).quality && (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Calidad: {(recording as { quality?: string; duration?: number }).quality} •{' '}
                      {(recording as { quality?: string; duration?: number }).duration?.toFixed(1)}s
                    </p>
                  )}
                </div>
              </div>

              <div className="text-right">
                {status === 'completed' && <StatusIndicator status="success" size="sm" />}
                {status === 'error' && <StatusIndicator status="error" size="sm" />}
                {status === 'pending' && <StatusIndicator status="pending" size="sm" />}
              </div>
            </div>
          );
        })}
      </div>

      {/* Información adicional */}
      {completedSteps > 0 && completedSteps < totalSteps && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-blue-800">
            <AlertCircle className="h-4 w-4 inline mr-2" />
            Continúa con los pasos restantes para completar tu registro de voz.
          </p>
        </div>
      )}

      {completedSteps === totalSteps && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-green-800">
            <Check className="h-4 w-4 inline mr-2" />
            ¡Excelente! Has completado todos los pasos. Tu perfil de voz está listo.
          </p>
        </div>
      )}

      {/* Botón de finalización */}
      {canSubmit && (
        <Button
          onClick={onSubmit}
          disabled={isSubmitting || completedSteps < totalSteps}
          loading={isSubmitting}
          className="w-full"
          size="lg"
        >
          {isSubmitting ? 'Procesando registro...' : 'Finalizar Registro'}
        </Button>
      )}

      {!canSubmit && completedSteps === totalSteps && (
        <div className="text-center text-gray-500 dark:text-gray-400">
          <p className="text-sm">Por favor, revisa todas las grabaciones antes de continuar.</p>
        </div>
      )}
    </Card>
  );
};

export default EnrollmentProgress;
