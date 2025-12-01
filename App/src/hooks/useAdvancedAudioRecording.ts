// @ts-nocheck - Este hook tiene muchas incompatibilidades de tipos del browser audio API
import { useState, useRef, useCallback, useEffect } from 'react';
import toast from 'react-hot-toast';

export interface AudioQuality {
  quality: string;
  duration: number;
  hasSilence: boolean;
  isValid: boolean;
}

interface AudioRecordingOptions {
  maxDuration?: number;
  minDuration?: number;
  onQualityCheck?: ((quality: AudioQuality) => void) | null;
  onRecordingComplete?: ((blob: Blob) => void) | null;
  autoStop?: boolean;
}

// Utilidades para el procesamiento de audio
const audioUtils = {
  // Convertir blob a formato compatible con el backend
  convertToWav: async (blob: Blob): Promise<Blob> => {
    // En un proyecto real, aquí podrías usar una librería como 'lamejs' o 'wav-encoder'
    // Por ahora retornamos el blob original
    return blob;
  },

  // Analizar calidad de audio básico
  analyzeAudioQuality: (audioBuffer: Float32Array): string => {
    let sum = 0;
    const length = audioBuffer.length;

    for (let i = 0; i < length; i++) {
      sum += Math.abs(audioBuffer[i]);
    }

    const average = sum / length;

    // Clasificar calidad basándose en el nivel promedio
    if (average > 0.1) return 'excellent';
    if (average > 0.05) return 'good';
    if (average > 0.02) return 'fair';
    return 'poor';
  },

  // Detectar si hay silencio
  detectSilence: (audioBuffer: Float32Array, threshold = 0.01): boolean => {
    let silentSamples = 0;
    const totalSamples = audioBuffer.length;

    for (let i = 0; i < totalSamples; i++) {
      if (Math.abs(audioBuffer[i]) < threshold) {
        silentSamples++;
      }
    }

    const silencePercentage = (silentSamples / totalSamples) * 100;
    return silencePercentage > 50; // Más del 50% es silencio
  },
};

export const useAdvancedAudioRecording = (options: AudioRecordingOptions = {}) => {
  const {
    maxDuration = 30, // Duración máxima en segundos
    minDuration = 2, // Duración mínima en segundos
    onQualityCheck = null,
    onRecordingComplete = null,
    autoStop = true,
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioQuality, setAudioQuality] = useState<AudioQuality | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [volume, setVolume] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const volumeIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Monitor de volumen en tiempo real
  const startVolumeMonitoring = useCallback(() => {
    if (!streamRef.current || !audioContextRef.current) return;

    const analyzer = audioContextRef.current.createAnalyser();
    const microphone = audioContextRef.current.createMediaStreamSource(streamRef.current);
    const bufferLength = analyzer.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    microphone.connect(analyzer);
    analyzerRef.current = analyzer;

    volumeIntervalRef.current = setInterval(() => {
      analyzer.getByteFrequencyData(dataArray);

      let sum = 0;
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i];
      }

      const average = sum / bufferLength;
      setVolume(Math.round((average / 255) * 100));
    }, 100);
  }, []);

  // Detener monitor de volumen
  const stopVolumeMonitoring = useCallback(() => {
    if (volumeIntervalRef.current) {
      clearInterval(volumeIntervalRef.current);
      volumeIntervalRef.current = null;
    }
    setVolume(0);
  }, []);

  // Iniciar grabación
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setRecordedBlob(null);
      setRecordingTime(0);
      setAudioQuality(null);
      setVolume(0);

      // Solicitar permisos de micrófono con configuración optimizada
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
          channelCount: 1,
        },
      });

      streamRef.current = stream;
      chunksRef.current = [];

      // Crear contexto de audio para análisis
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();

      // Determinar mimeType compatible
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        console.warn('audio/webm;codecs=opus not supported, trying audio/webm');
        mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          console.warn('audio/webm not supported, using default');
          mimeType = '';
        }
      }

      // Crear MediaRecorder con configuración optimizada
      const options: MediaRecorderOptions = mimeType
        ? { mimeType, audioBitsPerSecond: 32000 }
        : { audioBitsPerSecond: 32000 };

      console.log('Creating MediaRecorder with options:', options);
      const mediaRecorder = new MediaRecorder(stream, options);

      mediaRecorderRef.current = mediaRecorder;

      // Manejar errores del MediaRecorder
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('Error en la grabación');
        toast.error('Error en la grabación');
      };

      // Manejar datos de grabación
      mediaRecorder.ondataavailable = (event) => {
        console.log('Data available, size:', event.data.size);
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Manejar fin de grabación
      mediaRecorder.onstop = async () => {
        console.log('MediaRecorder stopped, recording time:', recordingTime);
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);

        // Analizar calidad de audio
        await analyzeRecording(blob);

        // Limpiar stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        // Cerrar contexto de audio
        if (audioContextRef.current) {
          await audioContextRef.current.close();
          audioContextRef.current = null;
        }

        stopVolumeMonitoring();

        if (onRecordingComplete) {
          onRecordingComplete(blob);
        }
      };

      // Manejar cambios de estado (para debugging)
      mediaRecorder.onstart = () => {
        console.log('MediaRecorder state changed to: recording');
      };

      mediaRecorder.onpause = () => {
        console.log('MediaRecorder state changed to: paused');
      };

      mediaRecorder.onresume = () => {
        console.log('MediaRecorder state changed to: recording (resumed)');
      };

      // Iniciar grabación
      console.log('Starting MediaRecorder...');
      console.log('MediaRecorder initial state:', mediaRecorder.state);
      mediaRecorder.start(100); // Capturar datos cada 100ms
      console.log('MediaRecorder state after start():', mediaRecorder.state);
      setIsRecording(true);
      setIsPaused(false);

      // Iniciar timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          const newTime = prev + 1;
          console.log('Recording time:', newTime);

          // Auto-stop si alcanza duración máxima
          if (autoStop && newTime >= maxDuration) {
            console.log('Max duration reached, stopping...');
            stopRecording();
            toast.info(`Grabación detenida automáticamente (${maxDuration}s máximo)`);
          }

          return newTime;
        });
      }, 1000);

      // Iniciar monitoreo de volumen
      startVolumeMonitoring();

      toast.success('Grabación iniciada');
      console.log('Recording started successfully');
    } catch (err) {
      let errorMessage = 'Error al acceder al micrófono';

      if (err.name === 'NotAllowedError') {
        errorMessage = 'Permisos de micrófono denegados';
      } else if (err.name === 'NotFoundError') {
        errorMessage = 'No se encontró micrófono';
      } else if (err.name === 'NotSupportedError') {
        errorMessage = 'Grabación no soportada en este navegador';
      }

      setError(errorMessage);
      toast.error(errorMessage);
    }
  }, [maxDuration, autoStop, onRecordingComplete, startVolumeMonitoring, stopVolumeMonitoring]);

  // Pausar/reanudar grabación
  const togglePause = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        setIsPaused(false);
        toast.success('Grabación reanudada');
      } else {
        mediaRecorderRef.current.pause();
        setIsPaused(true);
        toast.success('Grabación pausada');
      }
    }
  }, [isRecording, isPaused]);

  // Detener grabación
  const stopRecording = useCallback(() => {
    console.log('stopRecording called, isRecording:', isRecording, 'recordingTime:', recordingTime);
    if (mediaRecorderRef.current && isRecording) {
      // Verificar duración mínima
      if (recordingTime < minDuration) {
        console.log('Recording too short, minimum:', minDuration, 'current:', recordingTime);
        toast.error(`Graba al menos ${minDuration} segundos`);
        return;
      }

      console.log('Stopping MediaRecorder...');
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);

      // Limpiar timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      toast.success('Grabación completada');
    }
  }, [isRecording, recordingTime, minDuration]);

  // Analizar grabación
  const analyzeRecording = useCallback(
    async (blob) => {
      if (!blob || !onQualityCheck) return;

      try {
        setIsAnalyzing(true);

        // Convertir blob a ArrayBuffer
        const arrayBuffer = await blob.arrayBuffer();
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

        // Obtener datos de audio
        const channelData = audioBuffer.getChannelData(0);

        // Analizar calidad
        const quality = audioUtils.analyzeAudioQuality(channelData);
        const hasSilence = audioUtils.detectSilence(channelData);

        const analysis = {
          quality,
          duration: audioBuffer.duration,
          sampleRate: audioBuffer.sampleRate,
          channels: audioBuffer.numberOfChannels,
          hasSilence,
          isValid: quality !== 'poor' && !hasSilence && audioBuffer.duration >= minDuration,
        };

        setAudioQuality(analysis);

        if (onQualityCheck) {
          onQualityCheck(analysis);
        }

        await audioContext.close();
      } catch (err) {
        console.error('Error analizando audio:', err);
        toast.error('Error al analizar la grabación');
      } finally {
        setIsAnalyzing(false);
      }
    },
    [onQualityCheck, minDuration]
  );

  // Limpiar grabación
  const clearRecording = useCallback(() => {
    setRecordedBlob(null);
    setRecordingTime(0);
    setAudioQuality(null);
    setError(null);
    setVolume(0);
  }, []);

  // Reproducir grabación
  const playRecording = useCallback(() => {
    if (recordedBlob) {
      const audio = new Audio(URL.createObjectURL(recordedBlob));
      audio.play().catch((err) => {
        console.error('Error reproduciendo audio:', err);
        toast.error('Error al reproducir audio');
      });
    }
  }, [recordedBlob]);

  // Formatear tiempo
  const formatTime = useCallback((seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Limpiar recursos
  const cleanup = useCallback(() => {
    if (isRecording) {
      stopRecording();
    }

    stopVolumeMonitoring();

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
  }, [isRecording, stopRecording, stopVolumeMonitoring]);

  // Cleanup al desmontar (sin dependencias para que solo se ejecute al desmontar)
  useEffect(() => {
    return () => {
      console.log('Component unmounting, running cleanup');
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      if (timerRef.current) {
        clearInterval(timerRef.current);
      }

      if (volumeIntervalRef.current) {
        clearInterval(volumeIntervalRef.current);
      }

      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
    };
  }, []); // Sin dependencias - solo ejecutar al desmontar

  return {
    // Estado
    isRecording,
    isPaused,
    recordedBlob,
    recordingTime: formatTime(recordingTime),
    rawRecordingTime: recordingTime,
    audioQuality,
    error,
    isAnalyzing,
    volume,
    hasRecording: Boolean(recordedBlob),
    canStop: isRecording && recordingTime >= minDuration,

    // Acciones
    startRecording,
    stopRecording,
    togglePause,
    clearRecording,
    playRecording,
    analyzeRecording: () => recordedBlob && analyzeRecording(recordedBlob),
    cleanup,

    // Utilidades
    formatTime,
    maxDuration,
    minDuration,
  };
};
