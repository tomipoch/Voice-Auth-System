import { useEffect, useRef, useState, useCallback } from 'react';

interface VADConfig {
  silenceThreshold?: number; // dB level to consider silence (-50 default)
  silenceDuration?: number; // ms of silence to consider speech ended (1500 default)
  minSpeechDuration?: number; // minimum ms of speech required (500 default)
  enabled?: boolean;
}

interface VADResult {
  isSpeaking: boolean;
  hasFinished: boolean;
  speechDuration: number;
  reset: () => void;
}

export const useVoiceActivityDetection = (
  audioStream: MediaStream | null,
  config: VADConfig = {}
): VADResult => {
  const {
    silenceThreshold = -50,
    silenceDuration = 1500,
    minSpeechDuration = 500,
    enabled = true,
  } = config;

  const [isSpeaking, setIsSpeaking] = useState(false);
  const [hasFinished, setHasFinished] = useState(false);
  const [speechDuration, setSpeechDuration] = useState(0);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const silenceStartRef = useRef<number | null>(null);
  const speechStartRef = useRef<number | null>(null);
  const lastSpeakingStateRef = useRef(false);

  const reset = useCallback(() => {
    setIsSpeaking(false);
    setHasFinished(false);
    setSpeechDuration(0);
    silenceStartRef.current = null;
    speechStartRef.current = null;
    lastSpeakingStateRef.current = false;
  }, []);

  useEffect(() => {
    if (!audioStream || !enabled) {
      return;
    }

    // Create audio context and analyser
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(audioStream);

    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.8;
    microphone.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;

    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    const detectVoiceActivity = () => {
      if (!analyserRef.current) return;

      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average volume
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;

      // Convert to dB (approximate)
      const db = 20 * Math.log10(average / 255);

      const currentlySpeaking = db > silenceThreshold;
      const now = Date.now();

      // Detect speech start
      if (currentlySpeaking && !lastSpeakingStateRef.current) {
        speechStartRef.current = now;
        silenceStartRef.current = null;
        setIsSpeaking(true);
      }

      // Detect speech end
      if (!currentlySpeaking && lastSpeakingStateRef.current) {
        if (!silenceStartRef.current) {
          silenceStartRef.current = now;
        }
      }

      // Check if silence duration exceeded
      if (silenceStartRef.current && now - silenceStartRef.current >= silenceDuration) {
        if (speechStartRef.current) {
          const totalSpeechDuration = silenceStartRef.current - speechStartRef.current;
          setSpeechDuration(totalSpeechDuration);

          // Only mark as finished if speech was long enough
          if (totalSpeechDuration >= minSpeechDuration) {
            setIsSpeaking(false);
            setHasFinished(true);
            return; // Stop analyzing
          }
        }
      }

      // Reset silence timer if speaking again
      if (currentlySpeaking && silenceStartRef.current) {
        silenceStartRef.current = null;
      }

      lastSpeakingStateRef.current = currentlySpeaking;

      // Continue analyzing if not finished
      if (!hasFinished) {
        animationFrameRef.current = requestAnimationFrame(detectVoiceActivity);
      }
    };

    // Start detection
    animationFrameRef.current = requestAnimationFrame(detectVoiceActivity);

    // Cleanup
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [audioStream, enabled, silenceThreshold, silenceDuration, minSpeechDuration, hasFinished]);

  return {
    isSpeaking,
    hasFinished,
    speechDuration,
    reset,
  };
};
