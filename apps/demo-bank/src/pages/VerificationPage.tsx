import { useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Building2, Mic, MicOff, ArrowLeft, Volume2, Loader2, Shield, CheckCircle, XCircle } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import type { PhraseSession, VerificationResult } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';

interface TransferData {
  recipient: string;
  accountType: string;
  accountNumber: string;
  bank: string;
  amount: number;
  description: string;
}

export default function VerificationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const transfer = (location.state as { transfer?: TransferData })?.transfer;

  const [session, setSession] = useState<PhraseSession | null>(null);
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [completedPhrases, setCompletedPhrases] = useState<number[]>([]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    if (!authService.isAuthenticated() || !transfer) {
      navigate('/dashboard');
      return;
    }
    loadPhrases();
  }, [navigate, transfer]);

  const loadPhrases = async () => {
    try {
      const phraseSession = await biometricService.getPhrases('verification', 3);
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
      const result = await biometricService.verifyVoice(
        audioBlob,
        currentPhrase.id,
        currentPhrase.text
      );

      setCompletedPhrases(prev => [...prev, currentPhraseIndex]);

      // Check if this is the last phrase
      if (currentPhraseIndex >= session.phrases.length - 1) {
        // Final verification result
        setVerificationResult(result);
        
        // Navigate to result page after delay
        setTimeout(() => {
          navigate('/result', { 
            state: { 
              transfer,
              verified: result.verified,
              confidence: result.confidence,
            } 
          });
        }, 2000);
      } else {
        // Move to next phrase
        if (result.verified) {
          toast.success('¡Voz verificada! Continúa con la siguiente frase');
        }
        setCurrentPhraseIndex(prev => prev + 1);
      }
    } catch (error: unknown) {
      console.error('Error verifying voice:', error);
      const message = error instanceof Error ? error.message : 'Error en la verificación';
      toast.error(message);
      
      // On error, redirect to failed result
      navigate('/result', { 
        state: { 
          transfer,
          verified: false,
          confidence: 0,
        } 
      });
    } finally {
      setProcessing(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const currentPhrase = session?.phrases[currentPhraseIndex];
  const progress = session ? ((completedPhrases.length) / session.phrases.length) * 100 : 0;

  if (!transfer) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#f7fafc]">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-linear-to-r from-[#1a365d] to-[#2c5282] text-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/transfer')}
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

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Transfer Summary */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 mb-8">
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
            <Shield className="w-4 h-4" />
            <span>Autorización requerida para:</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-semibold text-gray-800 text-lg">{transfer.recipient}</p>
              <p className="text-sm text-gray-500">{transfer.bank} • Cuenta {transfer.accountType}</p>
            </div>
            <p className="text-2xl font-bold text-[#1a365d]">{formatCurrency(transfer.amount)}</p>
          </div>
        </div>

        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-[#1a365d]/10 rounded-2xl mb-4">
            <Mic className="w-7 h-7 text-[#1a365d]" />
          </div>
          <h1 className="text-xl font-bold text-gray-800 mb-2">Verificación por Voz</h1>
          <p className="text-gray-600">Lee las frases en voz alta para confirmar tu identidad</p>
        </div>

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

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-[#1a365d] animate-spin" />
          </div>
        ) : verificationResult ? (
          <div className={`rounded-2xl p-8 text-center border-2 ${
            verificationResult.verified 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            {verificationResult.verified ? (
              <>
                <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-green-800 mb-2">¡Identidad Verificada!</h2>
                <p className="text-green-600">Redirigiendo...</p>
              </>
            ) : (
              <>
                <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <h2 className="text-xl font-bold text-red-800 mb-2">Verificación Fallida</h2>
                <p className="text-red-600">No se pudo confirmar tu identidad</p>
              </>
            )}
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-gray-200 p-6">
            {/* Phrase Display */}
            <div className="mb-6">
              <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                <Volume2 className="w-4 h-4" />
                <span>Frase {currentPhraseIndex + 1} de {session?.phrases.length}</span>
              </div>
              <p className="text-lg font-medium text-gray-800 leading-relaxed bg-gray-50 rounded-xl p-5 border border-gray-100">
                "{currentPhrase?.text}"
              </p>
            </div>

            {/* Recording Button */}
            <div className="flex flex-col items-center">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                disabled={processing}
                className={`w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 ${
                  processing
                    ? 'bg-gray-200 cursor-not-allowed'
                    : isRecording
                      ? 'bg-red-500 hover:bg-red-600 animate-pulse'
                      : 'bg-[#1a365d] hover:bg-[#2c5282]'
                } shadow-lg`}
              >
                {processing ? (
                  <Loader2 className="w-8 h-8 text-gray-400 animate-spin" />
                ) : isRecording ? (
                  <MicOff className="w-8 h-8 text-white" />
                ) : (
                  <Mic className="w-8 h-8 text-white" />
                )}
              </button>
              <p className="mt-3 text-sm text-gray-600">
                {processing
                  ? 'Verificando...'
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
