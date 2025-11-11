import { useState } from 'react';
import { 
  Mic, 
  Square, 
  Play, 
  Pause, 
  RotateCcw, 
  Volume2, 
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { useAdvancedAudioRecording } from '../../hooks/useAdvancedAudioRecording';
import Button from '../ui/Button';
import Card from '../ui/Card';

const AudioRecorder = ({
  onRecordingComplete,
  onQualityCheck,
  maxDuration = 30,
  minDuration = 2,
  showQualityAnalysis = true,
  className = ''
}) => {
  const [hasStarted, setHasStarted] = useState(false);

  const {
    isRecording,
    isPaused,
    recordingTime,
    rawRecordingTime,
    audioQuality,
    error,
    isAnalyzing,
    volume,
    hasRecording,
    canStop,
    startRecording,
    stopRecording,
    togglePause,
    clearRecording,
    playRecording,
  } = useAdvancedAudioRecording({
    maxDuration,
    minDuration,
    onRecordingComplete,
    onQualityCheck,
  });

  const handleStartRecording = async () => {
    setHasStarted(true);
    await startRecording();
  };

  const getVolumeColor = () => {
    if (volume < 20) return 'bg-red-500';
    if (volume < 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getQualityColor = (quality) => {
    switch (quality) {
      case 'excellent': return 'text-green-600';
      case 'good': return 'text-blue-600';
      case 'fair': return 'text-yellow-600';
      case 'poor': return 'text-red-600';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getQualityIcon = (quality) => {
    switch (quality) {
      case 'excellent':
      case 'good':
        return <CheckCircle className="h-5 w-5" />;
      case 'fair':
        return <AlertCircle className="h-5 w-5" />;
      case 'poor':
        return <XCircle className="h-5 w-5" />;
      default:
        return null;
    }
  };

  return (
    <Card className={`p-6 ${className}`}>
      <div className="text-center space-y-6">
        {/* Indicador visual principal */}
        <div className="relative">
          <div className={`w-24 h-24 rounded-full mx-auto flex items-center justify-center transition-all duration-300 ${
            isRecording 
              ? isPaused
                ? 'bg-yellow-100 animate-pulse'
                : 'bg-red-100 animate-pulse'
              : hasRecording
                ? 'bg-green-100'
                : 'bg-blue-100'
          }`}>
            <Mic className={`h-12 w-12 transition-colors duration-300 ${
              isRecording 
                ? isPaused
                  ? 'text-yellow-600'
                  : 'text-red-600'
                : hasRecording
                  ? 'text-green-600'
                  : 'text-blue-600'
            }`} />
          </div>

          {/* Indicador de volumen */}
          {isRecording && !isPaused && (
            <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
              <div className="flex items-center space-x-1">
                <Volume2 className="h-3 w-3 text-gray-400" />
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-100 ${getVolumeColor()}`}
                    style={{ width: `${volume}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Tiempo de grabación */}
        {(isRecording || hasRecording) && (
          <div className="text-2xl font-mono font-bold text-gray-900 dark:text-gray-100">
            {recordingTime}
            {isRecording && (
              <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                / {Math.floor(maxDuration / 60).toString().padStart(2, '0')}:{(maxDuration % 60).toString().padStart(2, '0')}
              </span>
            )}
          </div>
        )}

        {/* Estado actual */}
        <div>
          {!hasStarted && (
            <p className="text-gray-600 dark:text-gray-400">
              Presiona el botón para comenzar a grabar
            </p>
          )}
          {isRecording && !isPaused && (
            <p className="text-red-600">
              Grabando... Habla claramente
            </p>
          )}
          {isRecording && isPaused && (
            <p className="text-yellow-600">
              Grabación pausada
            </p>
          )}
          {hasRecording && !isRecording && (
            <p className="text-green-600">
              Grabación completada
            </p>
          )}
          {error && (
            <p className="text-red-600 flex items-center justify-center">
              <AlertCircle className="h-4 w-4 mr-2" />
              {error}
            </p>
          )}
        </div>

        {/* Controles de grabación */}
        <div className="flex justify-center space-x-3">
          {!isRecording && !hasRecording && (
            <Button
              size="lg"
              onClick={handleStartRecording}
              className="px-8"
            >
              <Mic className="h-5 w-5 mr-2" />
              Iniciar Grabación
            </Button>
          )}

          {isRecording && (
            <>
              <Button
                variant="secondary"
                onClick={togglePause}
                size="lg"
              >
                {isPaused ? (
                  <>
                    <Play className="h-5 w-5 mr-2" />
                    Reanudar
                  </>
                ) : (
                  <>
                    <Pause className="h-5 w-5 mr-2" />
                    Pausar
                  </>
                )}
              </Button>

              <Button
                variant="danger"
                onClick={stopRecording}
                disabled={!canStop}
                size="lg"
              >
                <Square className="h-5 w-5 mr-2" />
                Detener
              </Button>
            </>
          )}

          {hasRecording && !isRecording && (
            <>
              <Button
                variant="secondary"
                onClick={playRecording}
                size="sm"
              >
                <Play className="h-4 w-4 mr-2" />
                Reproducir
              </Button>

              <Button
                variant="secondary"
                onClick={clearRecording}
                size="sm"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Nuevo
              </Button>
            </>
          )}
        </div>

        {/* Análisis de calidad */}
        {showQualityAnalysis && (isAnalyzing || audioQuality) && (
          <Card className="bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 p-4">
            <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
              Análisis de Calidad
            </h4>
            
            {isAnalyzing ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600 dark:text-gray-400">Analizando audio...</span>
              </div>
            ) : audioQuality && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Calidad:</span>
                  <div className={`flex items-center space-x-1 ${getQualityColor(audioQuality.quality)}`}>
                    {getQualityIcon(audioQuality.quality)}
                    <span className="text-sm font-medium capitalize">
                      {audioQuality.quality}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Duración:</span>
                  <span className="text-sm">
                    {audioQuality.duration?.toFixed(1)}s
                  </span>
                </div>

                {audioQuality.hasSilence && (
                  <div className="flex items-center justify-center space-x-1 text-orange-600">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-xs">Se detectó mucho silencio</span>
                  </div>
                )}

                {!audioQuality.isValid && (
                  <div className="flex items-center justify-center space-x-1 text-red-600">
                    <XCircle className="h-4 w-4" />
                    <span className="text-xs">Calidad insuficiente, graba nuevamente</span>
                  </div>
                )}
              </div>
            )}
          </Card>
        )}

        {/* Consejos */}
        {!hasRecording && hasStarted && (
          <Card className="bg-blue-50 border-blue-200 p-4">
            <p className="text-sm text-blue-800">
              💡 Habla de forma natural y clara, mantén una distancia apropiada del micrófono
            </p>
          </Card>
        )}

        {/* Indicador de progreso */}
        {isRecording && (
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div 
              className="bg-blue-600 h-1.5 rounded-full transition-all duration-1000"
              style={{ width: `${(rawRecordingTime / maxDuration) * 100}%` }}
            />
          </div>
        )}
      </div>
    </Card>
  );
};

export default AudioRecorder;