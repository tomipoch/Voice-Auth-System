import { useState } from 'react';
import { Shield, CheckCircle, XCircle, AlertTriangle, RotateCcw, Clock } from 'lucide-react';
import AudioRecorder from '../ui/AudioRecorder';
import Button from '../ui/Button';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';

const VoiceVerification = ({ 
  challenge, 
  onVerificationComplete, 
  maxAttempts = 3,
  className 
}) => {
  const [currentAttempt, setCurrentAttempt] = useState(0);
  const [verificationState, setVerificationState] = useState(challenge ? 'ready' : 'loading');
  const [verificationResult, setVerificationResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRecordingComplete = async (audioData, quality) => {
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
        setCurrentAttempt(prev => prev + 1);
        if (currentAttempt + 1 >= maxAttempts) {
          setVerificationState('blocked');
        } else {
          setVerificationState('failed');
        }
      }
    } catch (error) {
      setError(error.message || 'Error durante la verificación');
      setVerificationState('failed');
      setCurrentAttempt(prev => prev + 1);
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
      case 'recording':
        return 'Grabando... habla claramente';
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
        <Clock className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Cargando desafío...
        </h3>
        <p className="text-gray-600">
          Espera mientras preparamos tu frase de verificación
        </p>
      </Card>
    );
  }

  return (
    <Card className={`p-6 ${className}`}>
      <div className="text-center mb-6">
        <div className={`w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center ${
          verificationState === 'success' 
            ? 'bg-green-100' 
            : verificationState === 'failed' || verificationState === 'blocked'
              ? 'bg-red-100'
              : verificationState === 'processing'
                ? 'bg-blue-100'
                : 'bg-gray-100'
        }`}>
          {verificationState === 'success' ? (
            <CheckCircle className="h-10 w-10 text-green-600" />
          ) : verificationState === 'failed' || verificationState === 'blocked' ? (
            <XCircle className="h-10 w-10 text-red-600" />
          ) : verificationState === 'processing' ? (
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          ) : (
            <Shield className="h-10 w-10 text-gray-600" />
          )}
        </div>
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Verificación por Voz
        </h2>
        
        <p className="text-gray-600 mb-4">
          {getVerificationMessage()}
        </p>

        {getStatusIndicator()}
      </div>

      {/* Frase de desafío */}
      {(verificationState === 'ready' || verificationState === 'recording') && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-6">
          <div className="text-center">
            <h3 className="text-sm font-medium text-blue-900 mb-2">
              Lee la siguiente frase:
            </h3>
            <p className="text-xl font-bold text-blue-900">
              "{challenge.phrase}"
            </p>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Grabador de audio */}
      {(verificationState === 'ready') && (
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
            <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
          </div>
          <p className="text-sm text-gray-600 mt-4">
            Esto puede tomar unos segundos...
          </p>
        </div>
      )}

      {/* Resultado de verificación */}
      {verificationResult && (verificationState === 'success' || verificationState === 'failed') && (
        <div className={`border rounded-lg p-4 mb-6 ${
          verificationState === 'success' 
            ? 'bg-green-50 border-green-200' 
            : 'bg-red-50 border-red-200'
        }`}>
          <h4 className={`text-sm font-medium mb-2 ${
            verificationState === 'success' ? 'text-green-900' : 'text-red-900'
          }`}>
            Resultado de la Verificación
          </h4>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className={verificationState === 'success' ? 'text-green-700' : 'text-red-700'}>
                Confianza:
              </span>
              <span className="font-medium ml-2">
                {(verificationResult.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className={verificationState === 'success' ? 'text-green-700' : 'text-red-700'}>
                Umbral:
              </span>
              <span className="font-medium ml-2">
                {(verificationResult.threshold * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Controles */}
      <div className="flex justify-center space-x-3">
        {(verificationState === 'failed' && currentAttempt < maxAttempts) && (
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
            <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <p className="text-green-600 font-medium">
              Acceso concedido
            </p>
          </div>
        )}
      </div>

      {/* Información de intentos */}
      {maxAttempts > 1 && currentAttempt > 0 && verificationState !== 'success' && (
        <div className="mt-4 text-center text-sm text-gray-600">
          Intento {currentAttempt} de {maxAttempts}
        </div>
      )}
    </Card>
  );
};

export default VoiceVerification;