import { useState } from 'react';
import { Mic, CheckCircle, AlertTriangle, RotateCcw } from 'lucide-react';
import AudioRecorder from '../ui/AudioRecorder';
import Button from '../ui/Button';
import Card from '../ui/Card';
import StatusIndicator from '../ui/StatusIndicator';

const VoiceEnrollmentStep = ({ 
  stepNumber, 
  phrase, 
  isActive, 
  isCompleted, 
  onRecordingComplete,
  onRetry,
  className 
}) => {
  const [localPhase, setLocalPhase] = useState('ready'); // ready, recording, completed, error
  const [qualityScore, setQualityScore] = useState(null);

  // Determinar la fase actual
  const currentPhase = isCompleted ? 'completed' : localPhase;

  const handleRecordingComplete = (audioData, quality) => {
    setQualityScore(quality);
    
    if (quality && quality.isValid) {
      setLocalPhase('completed');
      onRecordingComplete(stepNumber, audioData, quality);
    } else {
      setLocalPhase('error');
    }
  };

  const handleRetry = () => {
    setLocalPhase('ready');
    setQualityScore(null);
    if (onRetry) {
      onRetry(stepNumber);
    }
  };

  if (!isActive && !isCompleted) {
    return (
      <Card className={`p-6 ${className} opacity-50`}>
        <div className="text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full mx-auto flex items-center justify-center mb-4">
            <span className="text-2xl font-bold text-gray-400">{stepNumber}</span>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Paso {stepNumber}
          </h3>
          <p className="text-gray-500 mb-4">"{phrase}"</p>
          <p className="text-sm text-gray-400">Completa los pasos anteriores</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-6 ${className} ${isActive ? 'ring-2 ring-blue-500' : ''}`}>
      <div className="text-center mb-6">
        <div className={`w-16 h-16 mx-auto flex items-center justify-center mb-4 rounded-full ${
          isCompleted 
            ? 'bg-green-100' 
            : isActive 
              ? 'bg-blue-100' 
              : 'bg-gray-100'
        }`}>
          {isCompleted ? (
            <CheckCircle className="h-8 w-8 text-green-600" />
          ) : (
            <span className={`text-2xl font-bold ${
              isActive ? 'text-blue-600' : 'text-gray-400'
            }`}>
              {stepNumber}
            </span>
          )}
        </div>
        
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Paso {stepNumber} de 5
        </h3>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <p className="text-lg font-medium text-blue-900">"{phrase}"</p>
          <p className="text-sm text-blue-700 mt-1">
            Lee esta frase de forma natural y clara
          </p>
        </div>
      </div>

      {currentPhase === 'ready' && (
        <div>
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            maxDuration={15}
            minDuration={2}
            showQualityAnalysis={true}
            className="border-0 shadow-none bg-transparent p-0"
          />
          
          <div className="mt-4 text-center">
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm text-yellow-800">
                <AlertTriangle className="h-4 w-4 inline mr-2" />
                Asegúrate de estar en un lugar silencioso
              </p>
            </div>
          </div>
        </div>
      )}

      {currentPhase === 'completed' && (
        <div className="text-center space-y-4">
          <StatusIndicator 
            status="success" 
            message="Grabación completada exitosamente" 
          />
          
          {qualityScore && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-green-900 mb-2">
                Calidad de la grabación
              </h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-green-700">Calidad:</span>
                  <span className="font-medium ml-2 capitalize">
                    {qualityScore.quality}
                  </span>
                </div>
                <div>
                  <span className="text-green-700">Duración:</span>
                  <span className="font-medium ml-2">
                    {qualityScore.duration?.toFixed(1)}s
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <Button
            variant="secondary"
            size="sm"
            onClick={handleRetry}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Grabar nuevamente
          </Button>
        </div>
      )}

      {currentPhase === 'error' && (
        <div className="text-center space-y-4">
          <StatusIndicator 
            status="error" 
            message="La calidad de la grabación es insuficiente" 
          />
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">
              Por favor, graba nuevamente asegurándote de:
            </p>
            <ul className="mt-2 text-sm text-red-700 list-disc list-inside text-left">
              <li>Hablar de forma clara y natural</li>
              <li>Estar en un ambiente silencioso</li>
              <li>Mantener una distancia adecuada del micrófono</li>
              <li>Leer la frase completa</li>
            </ul>
          </div>
          
          <Button onClick={handleRetry}>
            <Mic className="h-4 w-4 mr-2" />
            Intentar nuevamente
          </Button>
        </div>
      )}
    </Card>
  );
};

export default VoiceEnrollmentStep;