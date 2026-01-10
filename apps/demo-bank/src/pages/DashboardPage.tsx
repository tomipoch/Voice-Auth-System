import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Building2,
  Wallet,
  ArrowUpRight,
  ArrowDownLeft,
  Send,
  Mic,
  LogOut,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  CreditCard,
} from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import type { EnrollmentStatus } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';

// Mock transactions
const mockTransactions = [
  { id: 1, type: 'income', description: 'Depósito Nómina', amount: 850000, date: '08 Ene 2025' },
  { id: 2, type: 'expense', description: 'Supermercado Líder', amount: -45230, date: '07 Ene 2025' },
  { id: 3, type: 'expense', description: 'Netflix', amount: -9990, date: '06 Ene 2025' },
  { id: 4, type: 'income', description: 'Transferencia recibida', amount: 150000, date: '05 Ene 2025' },
  { id: 5, type: 'expense', description: 'Farmacia Cruz Verde', amount: -12500, date: '04 Ene 2025' },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const user = authService.getUser();
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    
    const loadEnrollmentStatus = async () => {
      try {
        const status = await biometricService.getEnrollmentStatus();
        setEnrollmentStatus(status);
      } catch (error) {
        console.error('Error checking enrollment status:', error);
      }
    };
    
    loadEnrollmentStatus();
  }, [navigate]);

  const handleLogout = () => {
    authService.logout();
    toast.success('Sesión cerrada');
    navigate('/');
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const isEnrolled = enrollmentStatus?.is_enrolled || enrollmentStatus?.enrollment_status === 'enrolled';

  return (
    <div className="min-h-screen bg-[#f7fafc]">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-gradient-to-r from-[#1a365d] to-[#2c5282] text-white">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center">
                <Building2 className="w-6 h-6 text-[#f6ad55]" />
              </div>
              <div>
                <h1 className="font-bold text-lg">Banco Pirulete</h1>
                <p className="text-blue-200 text-sm">Banca Digital</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-blue-200">
                Hola, {user?.first_name || 'Usuario'}
              </span>
              <button
                onClick={handleLogout}
                className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                title="Cerrar sesión"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Balance Card */}
        <div className="bg-gradient-to-br from-[#1a365d] to-[#2c5282] rounded-2xl p-6 text-white mb-8 shadow-xl">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-blue-200 text-sm mb-1">Saldo disponible</p>
              <h2 className="text-4xl font-bold mb-4">{formatCurrency(1500000)}</h2>
              <div className="flex items-center gap-2 text-sm text-blue-200">
                <CreditCard className="w-4 h-4" />
                <span>Cuenta Corriente ****4521</span>
              </div>
            </div>
            <div className="flex items-center gap-2 bg-white/10 px-3 py-1.5 rounded-full">
              <TrendingUp className="w-4 h-4 text-[#48bb78]" />
              <span className="text-sm">+12.5%</span>
            </div>
          </div>
        </div>

        {/* Biometric Status Card */}
        <div className={`rounded-2xl p-6 mb-8 border-2 ${
          isEnrolled 
            ? 'bg-green-50 border-green-200' 
            : 'bg-orange-50 border-orange-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                isEnrolled ? 'bg-green-100' : 'bg-orange-100'
              }`}>
                {isEnrolled ? (
                  <CheckCircle className="w-6 h-6 text-green-600" />
                ) : (
                  <AlertCircle className="w-6 h-6 text-orange-600" />
                )}
              </div>
              <div>
                <h3 className={`font-semibold ${isEnrolled ? 'text-green-800' : 'text-orange-800'}`}>
                  {isEnrolled ? 'Voz biométrica registrada' : 'Voz biométrica no registrada'}
                </h3>
                <p className={`text-sm ${isEnrolled ? 'text-green-600' : 'text-orange-600'}`}>
                  {isEnrolled 
                    ? 'Puedes autorizar transacciones con tu voz' 
                    : 'Registra tu voz para autorizar transacciones'
                  }
                </p>
              </div>
            </div>
            {!isEnrolled && (
              <button
                onClick={() => navigate('/enroll')}
                className="flex items-center gap-2 bg-[#1a365d] hover:bg-[#2c5282] text-white px-6 py-3 rounded-xl font-medium transition-colors"
              >
                <Mic className="w-5 h-5" />
                Registrar mi voz
              </button>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Quick Actions */}
          <div className="lg:col-span-1">
            <h3 className="font-semibold text-gray-800 mb-4">Acciones rápidas</h3>
            <div className="space-y-3">
              <button
                onClick={() => {
                  if (!isEnrolled) {
                    toast.error('Primero debes registrar tu voz biométrica');
                    return;
                  }
                  navigate('/transfer');
                }}
                className="w-full flex items-center gap-4 bg-white p-4 rounded-xl border border-gray-100 hover:border-[#1a365d]/30 hover:shadow-md transition-all group"
              >
                <div className="w-12 h-12 bg-[#1a365d]/10 rounded-xl flex items-center justify-center group-hover:bg-[#1a365d] transition-colors">
                  <Send className="w-5 h-5 text-[#1a365d] group-hover:text-white transition-colors" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-gray-800">Nueva Transferencia</p>
                  <p className="text-sm text-gray-500">Envía dinero al instante</p>
                </div>
              </button>

              <button className="w-full flex items-center gap-4 bg-white p-4 rounded-xl border border-gray-100 hover:border-[#1a365d]/30 hover:shadow-md transition-all group opacity-50 cursor-not-allowed">
                <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center">
                  <Wallet className="w-5 h-5 text-gray-400" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-gray-400">Pagar Servicios</p>
                  <p className="text-sm text-gray-400">Próximamente</p>
                </div>
              </button>
            </div>
          </div>

          {/* Recent Transactions */}
          <div className="lg:col-span-2">
            <h3 className="font-semibold text-gray-800 mb-4">Últimos movimientos</h3>
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              {mockTransactions.map((tx, index) => (
                <div
                  key={tx.id}
                  className={`flex items-center justify-between p-4 ${
                    index !== mockTransactions.length - 1 ? 'border-b border-gray-100' : ''
                  }`}
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                      tx.type === 'income' ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {tx.type === 'income' ? (
                        <ArrowDownLeft className="w-5 h-5 text-green-600" />
                      ) : (
                        <ArrowUpRight className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                    <div>
                      <p className="font-medium text-gray-800">{tx.description}</p>
                      <p className="text-sm text-gray-500">{tx.date}</p>
                    </div>
                  </div>
                  <span className={`font-semibold ${
                    tx.amount > 0 ? 'text-green-600' : 'text-gray-800'
                  }`}>
                    {tx.amount > 0 ? '+' : ''}{formatCurrency(tx.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
