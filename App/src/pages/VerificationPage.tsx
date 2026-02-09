import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import MainLayout from '../components/ui/MainLayout';
import VerificationWelcomeScreen from '../components/verification/VerificationWelcomeScreen';
import DynamicVerificationMulti from '../components/verification/DynamicVerificationMulti';
import { type VerifyPhraseResponse } from '../services/verificationService';
import Button from '../components/ui/Button';
import Card from '../components/ui/Card';

import Modal from '../components/ui/Modal';

type VerificationPhase = 'welcome' | 'verifying' | 'success' | 'failed' | 'error';

const VerificationPage = () => {
  const { user } = useAuth();
  const [phase, setPhase] = useState<VerificationPhase>('welcome');
  const [verificationResult, setVerificationResult] = useState<VerifyPhraseResponse | null>(null);
  const [showCancelModal, setShowCancelModal] = useState(false);

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

  const handleCancel = () => {
    setShowCancelModal(true);
  };

  const confirmCancel = () => {
    setShowCancelModal(false);
    setPhase('welcome');
    setVerificationResult(null);
  };

  return (
    <MainLayout>
      {/* Title */}
      <div className="text-left mb-8">
        <h1 className="text-4xl font-bold bg-linear-to-r from-gray-800 via-blue-700 to-green-800 dark:from-gray-200 dark:via-blue-400/70 dark:to-green-400/70 bg-clip-text text-transparent mb-4">
          Verificación de Identidad
        </h1>
        <p className="text-lg text-blue-600/80 font-medium max-w-2xl">
          {phase === 'welcome'
            ? 'Verifica tu identidad de forma segura usando tu voz'
            : phase === 'verifying'
              ? 'Lee las frases que aparecen en pantalla con tu voz natural'
              : 'Resultado de la verificación.'}
        </p>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto min-h-[calc(100vh-16rem)] flex flex-col justify-center">
        {phase === 'welcome' && <VerificationWelcomeScreen onStart={handleStart} />}

        {phase === 'verifying' && user && (
          <DynamicVerificationMulti
            key={user.id}
            userId={user.id}
            onVerificationSuccess={handleVerificationSuccess}
            onVerificationFailed={handleVerificationFailed}
            onCancel={handleCancel}
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

      {/* Cancel Confirmation Modal */}
      <Modal
        isOpen={showCancelModal}
        onClose={() => setShowCancelModal(false)}
        title="¿Cancelar verificación?"
        size="small"
      >
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            ¿Estás seguro de que quieres cancelar el proceso de verificación? Se perderá el progreso
            actual.
          </p>
          <div className="flex justify-center gap-4">
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

export default VerificationPage;
