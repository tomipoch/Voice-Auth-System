import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, User, Briefcase, DollarSign, AlertCircle } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import type { EnrollmentStatus } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';
import Header from '../components/Header';

export default function TransferPage() {
  const navigate = useNavigate();
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  const [formData, setFormData] = useState({
    recipient: 'Juan Pérez',
    accountType: 'corriente',
    accountNumber: '12345678',
    bank: 'Banco Estado',
    amount: '15000',
    description: 'Pago servicios',
  });

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    
    const loadStatus = async () => {
      try {
        const status = await biometricService.getEnrollmentStatus();
        setEnrollmentStatus(status);
      } catch (error) {
        console.error('Error loading enrollment status:', error);
      }
    };
    loadStatus();
  }, [navigate]);

  const isEnrolled = enrollmentStatus?.is_enrolled || enrollmentStatus?.enrollment_status === 'enrolled';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }

    // Validate amount
    const amount = parseInt(formData.amount);
    if (isNaN(amount) || amount <= 0) {
      toast.error('Ingresa un monto válido');
      return;
    }

    // Navigate to verification with transfer data
    navigate('/verify', { 
      state: { 
        transfer: {
          ...formData,
          amount: amount,
        }
      } 
    });
  };

  const formatCurrency = (value: string) => {
    const num = parseInt(value.replace(/\D/g, ''));
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('es-CL').format(num);
  };

  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      <Toaster position="top-right" />
      
      <Header showNav={true} isEnrolled={isEnrolled} />

      <main className="max-w-xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a365d]/10 rounded-2xl mb-4">
            <Send className="w-8 h-8 text-[#1a365d]" />
          </div>
          <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Nueva Transferencia</h1>
          <p className="text-gray-600">Ingresa los datos del destinatario</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-6">
          {/* Recipient */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Nombre del destinatario
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={formData.recipient}
                onChange={(e) => setFormData({ ...formData, recipient: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#1a365d]/20 focus:border-[#1a365d] transition-all outline-none"
                required
              />
            </div>
          </div>

          {/* Account Type */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Tipo de cuenta
              </label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <select
                  value={formData.accountType}
                  onChange={(e) => setFormData({ ...formData, accountType: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#1a365d]/20 focus:border-[#1a365d] transition-all outline-none appearance-none bg-white"
                >
                  <option value="corriente">Cuenta Corriente</option>
                  <option value="vista">Cuenta Vista</option>
                  <option value="ahorro">Cuenta Ahorro</option>
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Número de cuenta
              </label>
              <input
                type="text"
                value={formData.accountNumber}
                onChange={(e) => setFormData({ ...formData, accountNumber: e.target.value })}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#1a365d]/20 focus:border-[#1a365d] transition-all outline-none"
                required
              />
            </div>
          </div>

          {/* Bank */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Banco destino
            </label>
            <select
              value={formData.bank}
              onChange={(e) => setFormData({ ...formData, bank: e.target.value })}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#1a365d]/20 focus:border-[#1a365d] transition-all outline-none appearance-none bg-white"
            >
              <option value="Banco Estado">Banco Estado</option>
              <option value="Banco Santander">Banco Santander</option>
              <option value="Banco de Chile">Banco de Chile</option>
              <option value="BCI">BCI</option>
              <option value="Banco Falabella">Banco Falabella</option>
            </select>
          </div>

          {/* Amount */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Monto a transferir
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value.replace(/\D/g, '') })}
                className="w-full pl-10 pr-16 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#1a365d]/20 focus:border-[#1a365d] transition-all outline-none text-lg font-semibold"
                placeholder="0"
                required
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">CLP</span>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              ${formatCurrency(formData.amount)} pesos chilenos
            </p>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Descripción (opcional)
            </label>
            <input
              type="text"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-[#1a365d]/20 focus:border-[#1a365d] transition-all outline-none"
              placeholder="Ej: Pago arriendo"
            />
          </div>

          {/* Security Notice */}
          <div className="bg-[#1a365d]/5 border border-[#1a365d]/10 rounded-xl p-4 flex gap-3">
            <AlertCircle className="w-5 h-5 text-[#1a365d] shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-[#1a365d] font-medium">Verificación biométrica requerida</p>
              <p className="text-sm text-gray-600">Deberás confirmar esta transacción con tu voz</p>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="w-full bg-gradient-to-r from-[#1a365d] to-[#2c5282] hover:from-[#2c5282] hover:to-[#1a365d] text-white font-semibold py-4 rounded-xl flex items-center justify-center gap-2 transition-all duration-300 shadow-lg hover:shadow-xl"
          >
            <Send className="w-5 h-5" />
            Continuar con Verificación
          </button>
        </form>
      </main>
    </div>
  );
}
