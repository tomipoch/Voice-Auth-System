import { useEffect, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Building2, CheckCircle, XCircle, ArrowRight, Home, Receipt, Calendar, User } from 'lucide-react';
import authService from '../services/authService';
import { Toaster } from 'react-hot-toast';

interface TransferData {
  recipient: string;
  accountType: string;
  accountNumber: string;
  bank: string;
  amount: number;
  description: string;
}

interface LocationState {
  transfer?: TransferData;
  verified?: boolean;
  confidence?: number;
}

export default function ResultPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LocationState;
  
  const transfer = state?.transfer;
  const verified = state?.verified ?? false;
  const confidence = state?.confidence ?? 0;

  // Generate stable values once
  const transactionId = useMemo(() => 
    `TRX-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substring(2, 6).toUpperCase()}`,
    []
  );

  const currentDate = useMemo(() => 
    new Date().toLocaleDateString('es-CL', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    []
  );

  useEffect(() => {
    if (!authService.isAuthenticated() || !transfer) {
      navigate('/dashboard');
    }
  }, [navigate, transfer]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  if (!transfer) {
    return null;
  }

  return (
    <div className="min-h-screen bg-[#f7fafc]">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-linear-to-r from-[#1a365d] to-[#2c5282] text-white">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <Building2 className="w-6 h-6 text-[#f6ad55]" />
            <span className="font-bold">Banco Pirulete</span>
          </div>
        </div>
      </header>

      <main className="max-w-xl mx-auto px-4 py-12">
        {/* Result Header */}
        <div className={`text-center mb-8 p-8 rounded-2xl ${
          verified 
            ? 'bg-linear-to-br from-green-50 to-emerald-50 border-2 border-green-200' 
            : 'bg-linear-to-br from-red-50 to-orange-50 border-2 border-red-200'
        }`}>
          <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${
            verified ? 'bg-green-100' : 'bg-red-100'
          }`}>
            {verified ? (
              <CheckCircle className="w-10 h-10 text-green-600" />
            ) : (
              <XCircle className="w-10 h-10 text-red-600" />
            )}
          </div>
          <h1 className={`text-2xl font-bold mb-2 ${verified ? 'text-green-800' : 'text-red-800'}`}>
            {verified ? '¡Transferencia Exitosa!' : 'Transferencia Rechazada'}
          </h1>
          <p className={verified ? 'text-green-600' : 'text-red-600'}>
            {verified 
              ? 'Tu transferencia ha sido procesada correctamente' 
              : 'No se pudo verificar tu identidad'
            }
          </p>
          {verified && confidence > 0 && (
            <div className="mt-4 inline-flex items-center gap-2 bg-white/50 px-4 py-2 rounded-full">
              <span className="text-sm text-gray-600">Confianza de verificación:</span>
              <span className="font-semibold text-green-700">{Math.round(confidence * 100)}%</span>
            </div>
          )}
        </div>

        {/* Transaction Details */}
        {verified && (
          <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden mb-8">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <Receipt className="w-5 h-5 text-gray-500" />
                <span className="font-semibold text-gray-700">Comprobante de Transferencia</span>
              </div>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-500">Número de operación</span>
                <span className="font-mono font-semibold text-gray-800">{transactionId}</span>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <div className="flex items-center gap-2 text-gray-500">
                  <Calendar className="w-4 h-4" />
                  <span>Fecha y hora</span>
                </div>
                <span className="text-gray-800 text-right text-sm">{currentDate}</span>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <div className="flex items-center gap-2 text-gray-500">
                  <User className="w-4 h-4" />
                  <span>Destinatario</span>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-800">{transfer.recipient}</p>
                  <p className="text-sm text-gray-500">{transfer.bank}</p>
                </div>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-500">Cuenta destino</span>
                <span className="text-gray-800">
                  {transfer.accountType === 'corriente' ? 'Cuenta Corriente' : 'Cuenta Vista'} ****{transfer.accountNumber.slice(-4)}
                </span>
              </div>
              
              <div className="flex justify-between items-center py-3 border-b border-gray-100">
                <span className="text-gray-500">Descripción</span>
                <span className="text-gray-800">{transfer.description || '-'}</span>
              </div>
              
              <div className="flex justify-between items-center py-4 bg-[#1a365d]/5 -mx-6 px-6 rounded-b-xl">
                <span className="font-semibold text-gray-700">Monto transferido</span>
                <span className="text-2xl font-bold text-[#1a365d]">{formatCurrency(transfer.amount)}</span>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="space-y-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full bg-linear-to-r from-[#1a365d] to-[#2c5282] hover:from-[#2c5282] hover:to-[#1a365d] text-white font-semibold py-4 rounded-xl flex items-center justify-center gap-2 transition-all duration-300 shadow-lg hover:shadow-xl"
          >
            <Home className="w-5 h-5" />
            Volver al Inicio
          </button>
          
          {verified && (
            <button
              onClick={() => navigate('/transfer')}
              className="w-full bg-white border-2 border-[#1a365d] text-[#1a365d] font-semibold py-4 rounded-xl flex items-center justify-center gap-2 transition-all hover:bg-[#1a365d]/5"
            >
              Nueva Transferencia
              <ArrowRight className="w-5 h-5" />
            </button>
          )}
        </div>
      </main>
    </div>
  );
}
