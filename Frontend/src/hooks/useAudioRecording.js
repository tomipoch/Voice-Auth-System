import { useState, useRef, useCallback } from 'react';
import toast from 'react-hot-toast';

export const useAudioRecording = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);

  // Iniciar grabación
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      setRecordedBlob(null);
      setRecordingTime(0);

      // Solicitar permisos de micrófono
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      });

      streamRef.current = stream;
      chunksRef.current = [];

      // Crear MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus',
      });

      mediaRecorderRef.current = mediaRecorder;

      // Manejar datos de grabación
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Manejar fin de grabación
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);
        
        // Limpiar stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
        }
      };

      // Iniciar grabación
      mediaRecorder.start();
      setIsRecording(true);

      // Iniciar timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      toast.success('Grabación iniciada');
    } catch (err) {
      const errorMessage = err.name === 'NotAllowedError' 
        ? 'Permisos de micrófono denegados'
        : 'Error al acceder al micrófono';
      
      setError(errorMessage);
      toast.error(errorMessage);
    }
  }, []);

  // Detener grabación
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      // Limpiar timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      toast.success('Grabación detenida');
    }
  }, [isRecording]);

  // Limpiar grabación
  const clearRecording = useCallback(() => {
    setRecordedBlob(null);
    setRecordingTime(0);
    setError(null);
  }, []);

  // Reproducir grabación
  const playRecording = useCallback(() => {
    if (recordedBlob) {
      const audio = new Audio(URL.createObjectURL(recordedBlob));
      audio.play();
    }
  }, [recordedBlob]);

  // Obtener duración de la grabación
  const getRecordingDuration = useCallback(() => {
    return recordingTime;
  }, [recordingTime]);

  // Verificar si hay audio grabado
  const hasRecording = Boolean(recordedBlob);

  // Formatear tiempo de grabación
  const formatTime = useCallback((seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Limpiar recursos al desmontar
  const cleanup = useCallback(() => {
    if (isRecording) {
      stopRecording();
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
  }, [isRecording, stopRecording]);

  return {
    isRecording,
    recordedBlob,
    recordingTime: formatTime(recordingTime),
    error,
    hasRecording,
    startRecording,
    stopRecording,
    clearRecording,
    playRecording,
    getRecordingDuration,
    cleanup,
  };
};