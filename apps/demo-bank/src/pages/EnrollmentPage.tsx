import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mic, MicOff, CheckCircle, Volume2, Loader2, Clock, AlertTriangle, ShieldCheck } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import type { EnrollmentStartResponse, EnrollmentStatus } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';
import Header from '../components/Header';

export default function EnrollmentPage() {
  const navigate = useNavigate();
  const [session, setSession] = useState<EnrollmentStartResponse | null>(null);
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [completedPhrases, setCompletedPhrases] = useState<number[]>([]);
  const [phraseExpiry, setPhraseExpiry] = useState<number>(300); // 5 minutos por defecto
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const expiryIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    checkEnrollmentAndLoad();
    
    return () => {
      if (expiryIntervalRef.current) {
        clearInterval(expiryIntervalRef.current);
      }
    };
  }, [navigate]);

  const checkEnrollmentAndLoad = async () => {
    try {
      // Verificar si ya está inscrito
      const status = await biometricService.getEnrollmentStatus();
      setEnrollmentStatus(status);
      
      if (status.is_enrolled || status.enrollment_status === 'enrolled') {
        toast.success('Ya tienes tu voz registrada');
        setTimeout(() => navigate('/dashboard'), 2000);
        return;
      }
      
      // Si no está inscrito, cargar frases
      await loadPhrases();
    } catch (error) {
      console.error('Error checking enrollment:', error);
      toast.error('Error al verificar estado de inscripción');
    } finally {
      setLoading(false);
    }
  };

  const loadPhrases = async () => {
    try {
      const enrollmentSession = await biometricService.startEnrollment();
      setSession(enrollmentSession);
      
      // Iniciar contador de expiración (5 minutos = 300 segundos)
      setPhraseExpiry(300);
      startExpiryTimer();
    } catch (error) {
      console.error('Error loading phrases:', error);
      toast.error('Error al cargar las frases');
    }
  };

  const startExpiryTimer = () => {
    if (expiryIntervalRef.current) {
      clearInterval(expiryIntervalRef.current);
    }
    
    expiryIntervalRef.current = setInterval(() => {
      setPhraseExpiry(prev => {
        if (prev <= 1) {
          clearInterval(expiryIntervalRef.current!);
          toast.error('Las frases han expirado. Recargando...');
          setTimeout(() => loadPhrases(), 1500);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
          if (expiryIntervalRef.current) {
            clearInterval(expiryIntervalRef.current);
          }
          toast.success('¡Registro de voz completado!');
          setTimeout(() => navigate('/dashboard'), 2000);
        }
      } else {
        toast.error(result.message || 'Error al procesar el audio');
      }
    } catch (error: unknown) {
      console.error('Error enrolling audio:', error);
      const message = error instanceof Error ? error.message : 'Error al enviar el audio';
      toast.error(message);
    } finally {
      setProcessing(false);
    }
  };

  const currentPhrase = session?.phrases[currentPhraseIndex];
  const progress = session ? ((completedPhrases.length) / session.phrases.length) * 100 : 0;
  const isComplete = session && completedPhrases.length === session.phrases.length;
  const isAlreadyEnrolled = enrollmentStatus?.is_enrolled || enrollmentStatus?.enrollment_status === 'enrolled';

  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      <Toaster position="top-right" />
      
      <Header showNav={false} isEnrolled={isAlreadyEnrolled} />

      <main className="max-w-2xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a365d]/10 rounded-2xl mb-4">
            <Mic className="w-8 h-8 text-[#1a365d]" />
          </div>
          <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Registro de Voz Biométrica</h1>
          <p className="text-gray-600">Lee las siguientes frases en voz alta para registrar tu voz</p>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-[#1a365d] animate-spin mb-4" />
            <p className="text-gray-500">Verificando estado de inscripción...</p>
          </div>
        ) : isAlreadyEnrolled ? (
          <div className="bg-linear-to-br from-[#48bb78]/5 to-[#48bb78]/10 border-2 border-[#48bb78]/20 rounded-2xl p-8 text-center">
            <ShieldCheck className="w-16 h-16 text-[#48bb78] mx-auto mb-4" />
            <h2 className="text-xl font-bold text-[#1a365d] mb-2">¡Ya tienes tu voz registrada!</h2>
            <p className="text-gray-600 mb-6">Tu biometría de voz está activa y protege tus transacciones.</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-[#1a365d] hover:bg-[#2c5282] text-white font-semibold px-6 py-3 rounded-xl transition-colors"
            >
              Volver al Dashboard
            </button>
          </div>
        ) : isComplete ? (
          <div className="bg-linear-to-br from-[#48bb78]/5 to-[#48bb78]/10 border-2 border-[#48bb78]/20 rounded-2xl p-8 text-center">
            <CheckCircle className="w-16 h-16 text-[#48bb78] mx-auto mb-4" />
            <h2 className="text-xl font-bold text-[#1a365d] mb-2">¡Registro Completado!</h2>
            <p className="text-gray-600">Tu voz ha sido registrada exitosamente</p>
          </div>
        ) : (
          <>
            {/* Progress Bar */}
            <div className="mb-6">
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

            {/* Expiry Timer */}
            <div className={`flex items-center justify-center gap-2 mb-6 py-2 px-4 rounded-lg ${
              phraseExpiry < 60 ? 'bg-red-50 text-red-600' : 'bg-[#f6ad55]/10 text-[#1a365d]'
            }`}>
              {phraseExpiry < 60 ? (
                <AlertTriangle className="w-4 h-4" />
              ) : (
                <Clock className="w-4 h-4" />
              )}
              <span className="text-sm font-medium">
                Tiempo restante: <span className="font-bold">{formatTime(phraseExpiry)}</span>
              </span>
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
              {/* Phrase Indicator Pills */}
              <div className="flex gap-2 p-4 border-b border-gray-100 bg-gray-50">
                {session?.phrases.map((_, idx) => (
                  <div 
                    key={idx}
                    className={`flex-1 h-2 rounded-full transition-all ${
                      completedPhrases.includes(idx) 
                        ? 'bg-[#48bb78]' 
                        : idx === currentPhraseIndex 
                          ? 'bg-[#1a365d]' 
                          : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>

              {/* Phrase Display */}
              <div className="p-8">
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                  <Volume2 className="w-4 h-4" />
                  <span className="font-medium">Frase {currentPhraseIndex + 1} de {session?.phrases.length}</span>
                </div>
                
                <div className="bg-linear-to-br from-[#1a365d]/5 to-[#2c5282]/5 rounded-xl p-6 border border-[#1a365d]/10 mb-8">
                  <p className="text-xl font-medium text-[#1a365d] leading-relaxed text-center">
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
                          ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-lg shadow-red-500/30'
                          : 'bg-[#1a365d] hover:bg-[#2c5282] shadow-lg shadow-[#1a365d]/30'
                    }`}
                  >
                    {processing ? (
                      <Loader2 className="w-10 h-10 text-gray-400 animate-spin" />
                    ) : isRecording ? (
                      <MicOff className="w-10 h-10 text-white" />
                    ) : (
                      <Mic className="w-10 h-10 text-white" />
                    )}
                  </button>
                  <p className="mt-4 text-sm text-gray-600 font-medium">
                    {processing
                      ? 'Procesando audio...'
                      : isRecording
                        ? 'Grabando... Presiona para detener'
                        : 'Presiona para grabar'
                    }
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
