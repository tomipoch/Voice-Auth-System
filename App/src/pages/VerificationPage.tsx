import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import MainLayout from '../components/ui/MainLayout';
import VerificationWelcomeScreen from '../components/verification/VerificationWelcomeScreen';
import DynamicVerificationMulti from '../components/verification/DynamicVerificationMulti';
import { type VerifyPhraseResponse } from '../services/verificationService';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

type VerificationPhase = 'welcome' | 'verifying' | 'success' | 'failed' | 'error';

const VerificationPage = () => {
  const { user } = useAuth();
  const [phase, setPhase] = useState<VerificationPhase>('welcome');
  const [verificationResult, setVerificationResult] = useState<VerifyPhraseResponse | null>(null);

  const handleStart = () => {
    setPhase('verifying');
  };

  const handleVerificationSuccess = (result: VerifyPhraseResponse) => {
    setVerificationResult(result);
    setPhase('success');
  };

  const handleVerificationFailed = (result: VerifyPhraseResponse) => {
    setVerificationResult(result);
    // DynamicVerification handles retries, so we only switch phase if needed
    // But for now, let's keep it simple and let DynamicVerification show the failed state
  };

  const handleRetry = () => {
    setPhase('verifying');
    setVerificationResult(null);
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
        <h1 className="text-4xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-green-800 dark:from-gray-200 dark:via-blue-400/70 dark:to-green-400/70 bg-clip-text text-transparent mb-4">
          Verificación de Identidad
        </h1>
        <p className="text-lg text-blue-600/80 font-medium max-w-2xl mx-auto">
          {phase === 'welcome'
            ? 'Verifica tu identidad de forma segura usando tu voz.'
            : phase === 'verifying'
              ? 'Sigue las instrucciones para verificar tu identidad.'
              : 'Resultado de la verificación.'}
        </p>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto">
        {phase === 'welcome' && <VerificationWelcomeScreen onStart={handleStart} />}

        {phase === 'verifying' && user && (
          <DynamicVerificationMulti
            key={user.id}
            userId={user.id}
            onVerificationSuccess={handleVerificationSuccess}
            onVerificationFailed={handleVerificationFailed}
            className="shadow-2xl"
          />
        )}

        {phase === 'success' && verificationResult && (
          <Card className="p-8 text-center">
            <h2 className="text-3xl font-bold text-green-600 mb-4">¡Verificación Exitosa!</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-8">
              Tu identidad ha sido confirmada con un score promedio del{' '}
              <span className="font-bold">
                {((verificationResult.average_score || 0) * 100).toFixed(1)}%
              </span>
            </p>
            <div className="flex justify-center space-x-4">
              <Link to="/dashboard">
                <Button size="lg">Ir al Dashboard</Button>
              </Link>
              <Button variant="outline" onClick={handleRetry}>
                Verificar Nuevamente
              </Button>
            </div>
          </Card>
        )}
      </div>
    </MainLayout>
  );
};

export default VerificationPage;
