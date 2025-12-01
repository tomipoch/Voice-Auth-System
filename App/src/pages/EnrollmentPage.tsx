import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import MainLayout from '../components/ui/MainLayout';
import EnrollmentWelcomeScreen from '../components/enrollment/EnrollmentWelcomeScreen';
import DynamicEnrollment from '../components/enrollment/DynamicEnrollment';
import EnrollmentCompletionScreen from '../components/enrollment/EnrollmentCompletionScreen';
import toast from 'react-hot-toast';

type EnrollmentPhase = 'welcome' | 'recording' | 'completed' | 'error';

const EnrollmentPage = () => {
  const { user } = useAuth();
  const [phase, setPhase] = useState<EnrollmentPhase>('welcome');
  const [error, setError] = useState<string | null>(null);
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
      {/* Header */}
      <div className="flex items-center mb-8">
        <Link
          to="/dashboard"
          className="flex items-center px-4 py-2 text-blue-600 dark:text-blue-400/70 hover:text-blue-700 dark:hover:text-blue-300 transition-all duration-300 bg-white dark:bg-gray-800/70 backdrop-blur-xl border border-blue-200/40 dark:border-gray-600/40 rounded-xl hover:bg-white dark:hover:bg-gray-800/80 hover:shadow-md"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Volver al Dashboard
        </Link>
      </div>

      {/* Title */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-indigo-800 dark:from-gray-200 dark:via-blue-400/70 dark:to-indigo-400/70 bg-clip-text text-transparent mb-4">
          Registro de Perfil de Voz
        </h1>
        {phase === 'welcome' && (
          <p className="text-lg text-blue-600/80 dark:text-blue-400/80 font-medium max-w-2xl mx-auto">
            Configura tu autenticación biométrica por voz de forma segura
          </p>
        )}
      </div>

      {/* Content based on phase */}
      {phase === 'welcome' && <EnrollmentWelcomeScreen onStart={handleStart} />}

      {phase === 'recording' && user && (
        <DynamicEnrollment
          userId={user.id}
          difficulty="medium"
          onEnrollmentComplete={handleEnrollmentComplete}
          onError={handleEnrollmentError}
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
    </MainLayout>
  );
};

export default EnrollmentPage;
