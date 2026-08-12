import { useState } from 'react';
import { Mic, Square, CheckCircle, Loader2 } from 'lucide-react';
import { useAdvancedAudioRecording, AudioQuality } from '../../hooks/useAdvancedAudioRecording';
import CountdownTimer from './CountdownTimer';
import Card from '../ui/Card';
import toast from 'react-hot-toast';

interface EnhancedAudioRecorderProps {
  phraseText: string;
  onRecordingComplete: (audioData: Blob, quality: AudioQuality) => void | Promise<void>;
  maxDuration?: number;
  minDuration?: number;
  className?: string;
}

type RecordingPhase = 'ready' | 'countdown' | 'recording' | 'processing' | 'completed';

const EnhancedAudioRecorder = ({
  phraseText,
  onRecordingComplete,
  maxDuration = 30,
  minDuration = 2,
  className = '',
}: EnhancedAudioRecorderProps) => {
  const [phase, setPhase] = useState<RecordingPhase>('ready');

  const { recordingTime, audioQuality, error, volume, startRecording, stopRecording } =
    useAdvancedAudioRecording({
      maxDuration,
      minDuration,
      onRecordingComplete: async (blob: Blob, quality: AudioQuality) => {
        console.log('onRecordingComplete called with blob size:', blob.size);
        console.log('Quality received:', quality);
        setPhase('processing');

        try {
          await onRecordingComplete(blob, quality);
          setPhase('completed');
        } catch (err) {
          console.error('Error in onRecordingComplete:', err);
          toast.error('Error al procesar la grabación');
          setPhase('ready');
        }
      },
    });

  // VAD desactivado temporalmente (el stream se maneja en el hook)
  // const {
  //   hasFinished,
  //   isSpeaking,
  //   reset: resetVAD,
  // } = useVoiceActivityDetection(audioStream, {
  //   enabled: phase === 'recording',
  //   silenceThreshold: -45,
  //   silenceDuration: 3000,
  //   minSpeechDuration: 2000,
  // });

  // Auto-stop cuando VAD detecta fin (DESACTIVADO - control manual)
  // useEffect(() => {
  //   if (hasFinished && isRecording) {
  //     console.log('VAD detected speech end, stopping recording');
  //     stopRecording();
  //   }
  // }, [hasFinished, isRecording, stopRecording]);

  // Iniciar countdown
  const handleStart = async () => {
    // Solo iniciar el countdown, el hook manejará el acceso al micrófono
    setPhase('countdown');
  };

  // Countdown completado → iniciar grabación
  const handleCountdownComplete = async () => {
    setPhase('recording');
    // resetVAD(); // Desactivado temporalmente
    await startRecording();
  };

  // Cleanup (ya no necesario, el hook maneja el cleanup)
  // useEffect(() => {
  //   return () => {
  //     if (audioStreamRef.current) {
  //       audioStreamRef.current.getTracks().forEach((track) => track.stop());
  //     }
  //   };
  // }, []);

  const getVolumeColor = () => {
    if (volume < 20) return 'bg-red-500';
    if (volume < 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <Card className={`p-6 ${className}`}>
      <div className="text-center space-y-6">
        {/* Phrase Display */}
        <div className="bg-linear-to-r from-blue-50/80 to-indigo-50/80 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200/40 dark:border-blue-700/40 rounded-2xl p-6 mb-6">
          <p className="text-xl font-semibold text-blue-900 dark:text-blue-100">"{phraseText}"</p>
        </div>

        {/* Phase-specific content */}
        {phase === 'ready' && (
          <>
            <div className="w-24 h-24 bg-blue-100 dark:bg-blue-900/30 rounded-full mx-auto flex items-center justify-center">
              <Mic className="h-12 w-12 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="text-gray-700 dark:text-gray-300">Presiona el botón para comenzar</p>
            <button
              onClick={handleStart}
              className="px-8 py-3 bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              <Mic className="h-5 w-5 inline mr-2" />
              Comenzar
            </button>
          </>
        )}

        {phase === 'countdown' && (
          <CountdownTimer seconds={5} onComplete={handleCountdownComplete} />
        )}

        {phase === 'recording' && (
          <>
            {/* Recording Indicator */}
            <div className="relative">
              <div className="w-24 h-24 bg-red-100 dark:bg-red-900/30 rounded-full mx-auto flex items-center justify-center animate-pulse">
                <Mic className="h-12 w-12 text-red-600 dark:text-red-400" />
              </div>

              {/* Volume Indicator */}
              <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2">
                <div className="flex items-center space-x-1">
                  <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-100 ${getVolumeColor()}`}
                      style={{ width: `${volume}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Recording Time */}
            <div className="text-2xl font-mono font-bold text-gray-900 dark:text-gray-100">
              {recordingTime}
            </div>

            {/* Status */}
            <div className="space-y-2">
              <p className="text-red-600 dark:text-red-400 font-medium">
                🔴 Grabando... Lee la frase
              </p>
              {/* isSpeaking desactivado temporalmente */}
              {/* {isSpeaking && (
                <p className="text-green-600 dark:text-green-400 text-sm">✓ Voz detectada</p>
              )} */}
            </div>

            {/* Manual Stop */}
            <button
              onClick={stopRecording}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl font-medium transition-colors duration-300"
            >
              <Square className="h-4 w-4 inline mr-2" />
              Detener
            </button>
          </>
        )}

        {phase === 'processing' && (
          <>
            <Loader2 className="w-12 h-12 mx-auto animate-spin text-blue-600 dark:text-blue-400" />
            <p className="text-gray-700 dark:text-gray-300">Procesando audio...</p>
          </>
        )}

        {phase === 'completed' && (
          <>
            <div className="w-24 h-24 bg-green-100 dark:bg-green-900/30 rounded-full mx-auto flex items-center justify-center">
              <CheckCircle className="h-12 w-12 text-green-600 dark:text-green-400" />
            </div>
            <p className="text-green-600 dark:text-green-400 font-medium">✓ Grabación completada</p>
            {audioQuality && (
              <div className="text-sm text-gray-700 dark:text-gray-300">
                Calidad: <span className="font-semibold capitalize">{audioQuality.quality}</span>
              </div>
            )}
          </>
        )}

        {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
      </div>
    </Card>
  );
};

export default EnhancedAudioRecorder;
