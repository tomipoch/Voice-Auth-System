import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import MainLayout from '../components/ui/MainLayout';
import EnrollmentWelcomeScreen from '../components/enrollment/EnrollmentWelcomeScreen';
import DynamicEnrollment from '../components/enrollment/DynamicEnrollment';
import EnrollmentCompletionScreen from '../components/enrollment/EnrollmentCompletionScreen';
import Modal from '../components/ui/Modal';
import Button from '../components/ui/Button';
import toast from 'react-hot-toast';

type EnrollmentPhase = 'welcome' | 'recording' | 'completed' | 'error';

const EnrollmentPage = () => {
  const { user } = useAuth();
  const [phase, setPhase] = useState<EnrollmentPhase>('welcome');
  const [error, setError] = useState<string | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [completionData, setCompletionData] = useState<{
    samplesRecorded?: number;
    qualityScore?: number;
  }>({});

  // Check if user already has voice profile
  useEffect(() => {
    if (user?.voice_template) {
      toast.success('Ya tienes un perfil de voz registrado');
    }
  }, [user]);

  const handleStart = () => {
    setPhase('recording');
    setError(null);
  };

  const handleCancel = () => {
    setShowCancelModal(true);
  };

  const confirmCancel = () => {
    setShowCancelModal(false);
    setPhase('welcome');
    setError(null);
    toast('Registro cancelado', { icon: 'ℹ️' });
  };

  const handleEnrollmentComplete = (voiceprintId: string, qualityScore: number) => {
    console.log('Enrollment completed:', { voiceprintId, qualityScore });
    setCompletionData({
      samplesRecorded: 3,
      qualityScore,
    });
    setPhase('completed');
    toast.success('¡Perfil de voz creado exitosamente!');
  };

  const handleEnrollmentError = (errorMessage: string) => {
    console.error('Enrollment error:', errorMessage);
    setError(errorMessage);
    setPhase('error');
    toast.error(errorMessage);
  };

  const handleRetry = () => {
    setPhase('welcome');
    setError(null);
  };

  return (
    <MainLayout>
      {/* Title */}
      <div className="text-left mb-8">
        <h1 className="text-4xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400/70 dark:to-indigo-400/70 bg-clip-text text-transparent mb-4">
          Registro de Perfil de Voz
        </h1>
        <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium max-w-2xl">
          {phase === 'welcome'
            ? 'Configura tu autenticación biométrica por voz de forma segura'
            : phase === 'recording'
            ? 'Sigue las instrucciones para registrar tu voz.'
            : 'Resultado del registro.'}
        </p>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto min-h-[calc(100vh-16rem)] flex flex-col justify-center">

        {phase === 'welcome' && <EnrollmentWelcomeScreen onStart={handleStart} />}

        {phase === 'recording' && user && (
          <DynamicEnrollment
            userId={user.id}
            difficulty="medium"
            onEnrollmentComplete={handleEnrollmentComplete}
            onError={handleEnrollmentError}
            onCancel={handleCancel}
          />
        )}

        {phase === 'completed' && (
          <EnrollmentCompletionScreen
            samplesRecorded={completionData.samplesRecorded}
            qualityScore={completionData.qualityScore}
          />
        )}

        {phase === 'error' && (
          <div className="max-w-2xl mx-auto">
            <div className="backdrop-blur-xl bg-red-50/80 dark:bg-red-900/20 border border-red-200/40 dark:border-red-700/40 rounded-2xl p-8 text-center">
              <h2 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
                Error en el Registro
              </h2>
              <p className="text-red-700 dark:text-red-300 mb-6">{error}</p>
              <button
                onClick={handleRetry}
                className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors duration-300"
              >
                Intentar Nuevamente
              </button>
            </div>
          </div>
        )}

      </div>

      {/* Cancel Confirmation Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="¿Cancelar registro?"
        size="small"
      >
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-300">
            Si cancelas ahora, perderás el progreso actual. ¿Estás seguro de que deseas volver al inicio?
          </p>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="ghost" onClick={() => setShowCancelModal(false)}>
              No, continuar
            </Button>
            <Button variant="danger" onClick={confirmCancel}>
              Sí, cancelar
            </Button>
          </div>
        </div>
      </Modal>
    </MainLayout>
  );
};

export default EnrollmentPage;
