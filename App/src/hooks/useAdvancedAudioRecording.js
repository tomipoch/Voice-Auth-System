import { useState, useRef, useCallback, useEffect } from 'react';
import toast from 'react-hot-toast';

// Utilidades para el procesamiento de audio
const audioUtils = {
  // Convertir blob a formato compatible con el backend
  convertToWav: async (blob) => {
    // En un proyecto real, aquí podrías usar una librería como 'lamejs' o 'wav-encoder'
    // Por ahora retornamos el blob original
    return blob;
  },

  // Analizar calidad de audio básico
  analyzeAudioQuality: (audioBuffer) => {
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
  detectSilence: (audioBuffer, threshold = 0.01) => {
    let silentSamples = 0;
    const totalSamples = audioBuffer.length;
    
    for (let i = 0; i < totalSamples; i++) {
      if (Math.abs(audioBuffer[i]) < threshold) {
        silentSamples++;
      }
    }
    
    const silencePercentage = (silentSamples / totalSamples) * 100;
    return silencePercentage > 50; // Más del 50% es silencio
  }
};

export const useAdvancedAudioRecording = (options = {}) => {
  const {
    maxDuration = 30, // Duración máxima en segundos
    minDuration = 2,  // Duración mínima en segundos
    onQualityCheck = null,
    onRecordingComplete = null,
    autoStop = true
  } = options;

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioQuality, setAudioQuality] = useState(null);
  const [error, setError] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [volume, setVolume] = useState(0);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const analyzerRef = useRef(null);
  const audioContextRef = useRef(null);
  const volumeIntervalRef = useRef(null);

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
      
      // Crear MediaRecorder con configuración optimizada
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
        audioBitsPerSecond: 32000,
      });

      mediaRecorderRef.current = mediaRecorder;

      // Manejar datos de grabación
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Manejar fin de grabación
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        
        // Analizar calidad de audio
        await analyzeRecording(blob);
        
        // Limpiar stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
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

      // Iniciar grabación
      mediaRecorder.start(100); // Capturar datos cada 100ms
      setIsRecording(true);
      setIsPaused(false);

      // Iniciar timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          
          // Auto-stop si alcanza duración máxima
          if (autoStop && newTime >= maxDuration) {
            stopRecording();
            toast.info(`Grabación detenida automáticamente (${maxDuration}s máximo)`);
          }
          
          return newTime;
        });
      }, 1000);

      // Iniciar monitoreo de volumen
      startVolumeMonitoring();

      toast.success('Grabación iniciada');
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
  }, [maxDuration, autoStop, onRecordingComplete, startVolumeMonitoring, stopVolumeMonitoring, analyzeRecording, stopRecording]);

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
    if (mediaRecorderRef.current && isRecording) {
      // Verificar duración mínima
      if (recordingTime < minDuration) {
        toast.error(`Graba al menos ${minDuration} segundos`);
        return;
      }

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
  const analyzeRecording = useCallback(async (blob) => {
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
        isValid: quality !== 'poor' && !hasSilence && audioBuffer.duration >= minDuration
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
  }, [onQualityCheck, minDuration]);

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
      audio.play().catch(err => {
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
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
  }, [isRecording, stopRecording, stopVolumeMonitoring]);

  // Cleanup al desmontar
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

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