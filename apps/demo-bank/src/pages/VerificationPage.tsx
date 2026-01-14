import { useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Building2, Mic, MicOff, ArrowLeft, Volume2, Loader2, Shield, CheckCircle, XCircle } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import api from '../services/api';
import type { StartMultiVerificationResponse, VerifyPhraseResponse } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';

interface TransferData {
  recipient: string;
  accountType: string;
  accountNumber: string;
  bank: string;
  amount: number;
  description: string;
}

interface ReturnData {
  formData: any;
  pin: string;
  selectedContact: any;
}

export default function VerificationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const transfer = (location.state as { transfer?: TransferData; returnData?: ReturnData })?.transfer;
  const returnData = (location.state as { transfer?: TransferData; returnData?: ReturnData })?.returnData;

  const [session, setSession] = useState<StartMultiVerificationResponse | null>(null);
  const [currentPhraseIndex, setCurrentPhraseIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [verificationResult, setVerificationResult] = useState<VerifyPhraseResponse | null>(null);
  const [completedPhrases, setCompletedPhrases] = useState<number[]>([]);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const hasInitialized = useRef(false);

  useEffect(() => {
    if (!authService.isAuthenticated() || !transfer) {
      navigate('/dashboard');
      return;
    }
    
    // Prevent double initialization in React StrictMode
    if (hasInitialized.current) return;
    hasInitialized.current = true;
    
    loadVerificationSession();
  }, [navigate, transfer]);

  const loadVerificationSession = async () => {
    try {
      const verificationSession = await biometricService.startMultiPhraseVerification('medium');
      setSession(verificationSession);
    } catch (error) {
      console.error('Error starting verification:', error);
      toast.error('Error al iniciar la verificación');
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
    
    const currentChallenge = session.challenges[currentPhraseIndex];
    if (!currentChallenge) return;
    
    setProcessing(true);

    try {
      const result = await biometricService.verifyPhrase(
        session.verification_id,
        currentChallenge.challenge_id,
        currentPhraseIndex + 1,
        audioBlob
      );

      setCompletedPhrases(prev => [...prev, currentPhraseIndex]);

      // Check if verification is complete
      if (result.is_complete) {
        // Final verification result
        setVerificationResult(result);
        
        // If returnData exists, execute the transfer automatically
        if (returnData && result.is_verified) {
          try {
            await api.post('/transfers/execute', {
              amount: returnData.formData.amount,
              recipient_first_name: returnData.formData.recipient_first_name,
              recipient_last_name: returnData.formData.recipient_last_name,
              recipient_rut: returnData.formData.recipient_rut,
              recipient_email: returnData.formData.recipient_email,
              recipient_account_number: returnData.formData.recipient_account_number,
              recipient_account_type: returnData.formData.recipient_account_type,
              recipient_bank: returnData.formData.recipient_bank,
              description: returnData.formData.description,
              pin: returnData.pin,
              verification_id: session.verification_id,
              save_contact: returnData.formData.save_contact && !returnData.selectedContact,
            });
            
            toast.success('¡Transferencia exitosa!');
            
            // Navigate to result page
            setTimeout(() => {
              navigate('/result', { 
                state: { 
                  transfer,
                  verified: true,
                  confidence: result.average_score || result.current_score || 0,
                  transferCompleted: true,
                } 
              });
            }, 2000);
          } catch (error: any) {
            toast.error(error.response?.data?.error || 'Error al realizar la transferencia');
            navigate('/result', { 
              state: { 
                transfer,
                verified: true,
                confidence: result.average_score || result.current_score || 0,
                transferCompleted: false,
                error: error.response?.data?.error || 'Error al realizar la transferencia'
              } 
            });
          }
        } else {
          // Original flow - just navigate to result
          setTimeout(() => {
            navigate('/result', { 
              state: { 
                transfer,
                verified: result.is_verified,
                confidence: result.average_score || result.current_score || 0,
              } 
            });
          }, 2000);
        }
      } else {
        // Move to next phrase
        if (result.success) {
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

  const currentPhrase = session?.challenges[currentPhraseIndex]?.phrase;
  const progress = session ? ((completedPhrases.length) / session.total_phrases) * 100 : 0;

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
              <span className="font-bold">Banco Familia</span>
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
            <span>{completedPhrases.length} de {session?.total_phrases || 3} frases</span>
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
            verificationResult.is_verified 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            {verificationResult.is_verified ? (
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
                <span>Frase {currentPhraseIndex + 1} de {session?.total_phrases}</span>
              </div>
              <p className="text-lg font-medium text-gray-800 leading-relaxed bg-gray-50 rounded-xl p-5 border border-gray-100">
                "{currentPhrase}"
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
