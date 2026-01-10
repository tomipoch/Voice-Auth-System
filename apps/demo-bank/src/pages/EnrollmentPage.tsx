import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Mic, MicOff, CheckCircle, ArrowLeft, Volume2, Loader2 } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import type { PhraseSession } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';

export default function EnrollmentPage() {
  const navigate = useNavigate();
  const [session, setSession] = useState<PhraseSession | null>(null);
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [completedPhrases, setCompletedPhrases] = useState<number[]>([]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    loadPhrases();
  }, [navigate]);

  const loadPhrases = async () => {
    try {
      const phraseSession = await biometricService.getPhrases('enrollment', 3);
      setSession(phraseSession);
    } catch (error) {
      console.error('Error loading phrases:', error);
      toast.error('Error al cargar las frases');
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        await processRecording(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('No se pudo acceder al micrófono');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processRecording = async (audioBlob: Blob) => {
    if (!session) return;
    
    const currentPhrase = session.phrases[currentPhraseIndex];
    setProcessing(true);

    try {
      const result = await biometricService.enrollAudio(
        audioBlob,
        currentPhrase.id,
        currentPhrase.text
      );

      if (result.success) {
        setCompletedPhrases(prev => [...prev, currentPhraseIndex]);
        
        if (currentPhraseIndex < session.phrases.length - 1) {
          toast.success('¡Frase registrada!');
          setCurrentPhraseIndex(prev => prev + 1);
        } else {
          toast.success('¡Registro de voz completado!');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      } else {
        toast.error(result.message || 'Error al procesar el audio');
      }
    } catch (error: any) {
      console.error('Error enrolling audio:', error);
      toast.error(error.response?.data?.detail || 'Error al enviar el audio');
    } finally {
      setProcessing(false);
    }
  };

  const currentPhrase = session?.phrases[currentPhraseIndex];
  const progress = session ? ((completedPhrases.length) / session.phrases.length) * 100 : 0;
  const isComplete = session && completedPhrases.length === session.phrases.length;

  return (
    <div className="min-h-screen bg-[#f7fafc]">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-linear-to-r from-[#1a365d] to-[#2c5282] text-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-3">
              <Building2 className="w-6 h-6 text-[#f6ad55]" />
              <span className="font-bold">Banco Pirulete</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a365d]/10 rounded-2xl mb-4">
            <Mic className="w-8 h-8 text-[#1a365d]" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Registro de Voz Biométrica</h1>
          <p className="text-gray-600">Lee las siguientes frases en voz alta para registrar tu voz</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progreso</span>
            <span>{completedPhrases.length} de {session?.phrases.length || 3} frases</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div 
              className="h-full bg-linear-to-r from-[#1a365d] to-[#2c5282] transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-[#1a365d] animate-spin" />
          </div>
        ) : isComplete ? (
          <div className="bg-green-50 border-2 border-green-200 rounded-2xl p-8 text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-green-800 mb-2">¡Registro Completado!</h2>
            <p className="text-green-600">Tu voz ha sido registrada exitosamente</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-200 p-8">
            {/* Phrase Display */}
            <div className="mb-8">
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                <Volume2 className="w-4 h-4" />
                <span>Frase {currentPhraseIndex + 1} de {session?.phrases.length}</span>
              </div>
              <p className="text-xl font-medium text-gray-800 leading-relaxed bg-gray-50 rounded-xl p-6 border border-gray-100">
                "{currentPhrase?.text}"
              </p>
            </div>

            {/* Recording Button */}
            <div className="flex flex-col items-center">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={processing}
                className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
                  processing
                    ? 'bg-gray-200 cursor-not-allowed'
                    : isRecording
                      ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                      : 'bg-[#1a365d] hover:bg-[#2c5282]'
                } shadow-lg`}
              >
                {processing ? (
                  <Loader2 className="w-10 h-10 text-gray-400 animate-spin" />
                ) : isRecording ? (
                  <MicOff className="w-10 h-10 text-white" />
                ) : (
                  <Mic className="w-10 h-10 text-white" />
                )}
              </button>
              <p className="mt-4 text-sm text-gray-600">
                {processing
                  ? 'Procesando...'
                  : isRecording
                    ? 'Grabando... Presiona para detener'
                    : 'Presiona para grabar'
                }
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
