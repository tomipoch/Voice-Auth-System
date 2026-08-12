import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Wallet,
  Send,
  Mic,
  CheckCircle,
  CreditCard as CardIcon,
  ShieldCheck,
  Eye,
  EyeOff,
  Star,
  Clock,
  Plus,
  User,
} from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import api from '../services/api';
import type { EnrollmentStatus } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';
import Header from '../components/Header';

// Mock data - Productos
const mockProducts = [
  { 
    id: 1, 
    type: 'Cuenta Corriente', 
    number: '1 981 155983 3',
    balanceContable: 1850420,
    balanceDisponible: 1850420,
  },
  { 
    id: 2, 
    type: 'Línea de Crédito', 
    number: '2 981 155983 8',
    cupoAutorizado: 500000,
    saldoUtilizado: 0,
    saldoDisponible: 500000,
  },
];

// Mock data - Últimos movimientos
const mockTransactions = [
  { id: 1, date: '12/01/2026', description: 'Pago Supermercado Líder', amount: -45230 },
  { id: 2, date: '12/01/2026', description: 'Transferencia Recibida', amount: 150000 },
  { id: 3, date: '11/01/2026', description: 'Pago Netflix', amount: -9990 },
  { id: 4, date: '11/01/2026', description: 'Pago Uber Trip', amount: -8500 },
  { id: 5, date: '10/01/2026', description: 'Depósito Nómina', amount: 1250000 },
];

// Mock data - Contactos favoritos (con datos completos para transferencias)
const mockContacts = [
  { 
    id: 1, 
    initials: 'PP', 
    name: 'Pia Poblete', 
    bank: 'Banco Familia',
    color: 'bg-blue-500',
    first_name: 'Pia',
    last_name: 'Poblete',
    rut: '18.572.849-8',
    email: 'piapobletech@gmail.com',
    account_type: 'Cuenta Corriente',
    account_number: '0001234568'
  },
  { 
    id: 2, 
    initials: 'AC', 
    name: 'Ana Chamorro', 
    bank: 'Banco Familia',
    color: 'bg-pink-500',
    first_name: 'Ana',
    last_name: 'Chamorro',
    rut: '9.555.737-6',
    email: 'anachamorromunoz@gmail.com',
    account_type: 'Cuenta Corriente',
    account_number: '0001234569'
  },
  { 
    id: 3, 
    initials: 'RP', 
    name: 'Raul Poblete', 
    bank: 'Banco Familia',
    color: 'bg-green-500',
    first_name: 'Raul',
    last_name: 'Poblete',
    rut: '8.385.075-2',
    email: 'rapomo3@gmail.com',
    account_type: 'Cuenta Corriente',
    account_number: '0001234570'
  },
];

export default function DashboardPage() {
  const navigate = useNavigate();
  const user = authService.getUser();
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  const [showBalances, setShowBalances] = useState(true);
  const [hasPin, setHasPin] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    
    const loadData = async () => {
      try {
        const [status, pinStatus] = await Promise.all([
          biometricService.getEnrollmentStatus(),
          api.get('/pin/status').then(res => res.data).catch(() => ({ has_pin: true }))
        ]);
        setEnrollmentStatus(status);
        setHasPin(pinStatus.has_pin);
      } catch (error) {
        console.error('Error loading data:', error);
      }
    };
    
    loadData();
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
    <div className="min-h-screen bg-[#f5f5f5]">
      <Toaster position="top-right" />
      
      <Header showNav={true} isEnrolled={isEnrolled} />

      <main className="max-w-7xl mx-auto px-6 py-8">
        
        {/* PIN Setup Alert - Priority alert */}
        {!hasPin && (
          <div className="bg-linear-to-r from-red-50 to-orange-50 border-l-4 border-red-500 rounded-r-lg p-4 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
                <ShieldCheck className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <h3 className="font-bold text-[#1a365d]">Configura tu PIN de Transferencias</h3>
                <p className="text-gray-600 text-sm">Para realizar transferencias necesitas configurar un PIN de 6 dígitos</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/setup-pin')}
              className="bg-red-500 hover:bg-red-600 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors"
            >
              Configurar PIN
            </button>
          </div>
        )}

        {/* Biometric Alert - Only show if not enrolled */}
        {!isEnrolled && (
          <div className="bg-linear-to-r from-[#f6ad55]/10 to-[#ed8936]/10 border-l-4 border-[#f6ad55] rounded-r-lg p-4 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-[#f6ad55]/20 rounded-full flex items-center justify-center">
                <Mic className="w-6 h-6 text-[#f6ad55]" />
              </div>
              <div>
                <h3 className="font-bold text-[#1a365d]">Activa la Seguridad Biométrica</h3>
                <p className="text-gray-600 text-sm">Registra tu voz para autorizar transferencias de forma segura</p>
              </div>
            </div>
            <button
              onClick={() => navigate('/enroll')}
              className="bg-[#f6ad55] hover:bg-[#ed8936] text-[#1a365d] font-semibold px-6 py-2.5 rounded-lg transition-colors"
            >
              Activar ahora
            </button>
          </div>
        )}

        {/* Section: Tus Productos */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-[#1a365d]">Tus Productos</h2>
            <button 
              onClick={() => setShowBalances(!showBalances)}
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-[#1a365d] transition-colors"
            >
              {showBalances ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
              {showBalances ? 'Ocultar saldos' : 'Mostrar saldos'}
            </button>
          </div>
          
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            {mockProducts.map((product, index) => (
              <div 
                key={product.id}
                className={`p-5 ${index !== mockProducts.length - 1 ? 'border-b border-gray-100' : ''}`}
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      product.type === 'Cuenta Corriente' ? 'bg-[#1a365d]/10' : 'bg-[#f6ad55]/10'
                    }`}>
                      {product.type === 'Cuenta Corriente' ? (
                        <Wallet className="w-5 h-5 text-[#1a365d]" />
                      ) : (
                        <CardIcon className="w-5 h-5 text-[#f6ad55]" />
                      )}
                    </div>
                    <div>
                      <p className="font-semibold text-[#1a365d]">{product.type}</p>
                      <p className="text-sm text-gray-500">{product.number}</p>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap items-center gap-4 lg:gap-8">
                    {product.type === 'Cuenta Corriente' ? (
                      <>
                        <div className="text-right">
                          <p className="text-xs text-gray-400">Saldo contable</p>
                          <p className="font-semibold text-gray-800">
                            {showBalances ? formatCurrency(product.balanceContable!) : '•••••••'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-400">Saldo disponible</p>
                          <p className="font-bold text-[#48bb78]">
                            {showBalances ? formatCurrency(product.balanceDisponible!) : '•••••••'}
                          </p>
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="text-right">
                          <p className="text-xs text-gray-400">Cupo autorizado</p>
                          <p className="font-semibold text-gray-800">
                            {showBalances ? formatCurrency(product.cupoAutorizado!) : '•••••••'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-400">Disponible</p>
                          <p className="font-bold text-[#48bb78]">
                            {showBalances ? formatCurrency(product.saldoDisponible!) : '•••••••'}
                          </p>
                        </div>
                      </>
                    )}
                    
                    <div className="flex gap-2">
                      <button className="px-4 py-2 text-sm font-medium text-[#1a365d] border border-[#1a365d]/30 rounded-lg hover:bg-[#1a365d]/5 transition-colors">
                        Movimientos
                      </button>
                      <button 
                        onClick={() => isEnrolled ? navigate('/transfer') : toast.error('Primero activa la seguridad biométrica')}
                        className="px-4 py-2 text-sm font-semibold text-white bg-[#f6ad55] hover:bg-[#ed8936] rounded-lg transition-colors"
                      >
                        Transferir
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Grid: Movimientos + Contactos + Seguridad */}
        <div className="grid lg:grid-cols-12 gap-6">
          
          {/* Últimos Movimientos */}
          <section className="lg:col-span-5">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-[#1a365d]" />
                  <h3 className="font-bold text-[#1a365d]">Últimos movimientos</h3>
                </div>
                <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">Cuenta Corriente</span>
              </div>
              
              <div className="space-y-3">
                {mockTransactions.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="text-xs text-gray-400">{tx.date}</p>
                      <p className="text-sm font-medium text-gray-800">{tx.description}</p>
                    </div>
                    <p className={`font-semibold ${tx.amount > 0 ? 'text-[#48bb78]' : 'text-gray-800'}`}>
                      {tx.amount > 0 ? '+' : ''}{formatCurrency(tx.amount)}
                    </p>
                  </div>
                ))}
              </div>
              
              <button className="w-full mt-4 text-center text-sm text-[#1a365d] font-medium hover:underline">
                Ir a movimientos
              </button>
            </div>
          </section>

          {/* Contactos Favoritos */}
          <section className="lg:col-span-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 h-full">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Star className="w-5 h-5 text-[#f6ad55]" />
                  <h3 className="font-bold text-[#1a365d]">Tus contactos favoritos</h3>
                </div>
              </div>
              
              <div className="space-y-3">
                {mockContacts.map((contact) => (
                  <div key={contact.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 ${contact.color} rounded-full flex items-center justify-center text-white font-bold text-sm`}>
                        {contact.initials}
                      </div>
                      <div>
                        <p className="font-medium text-gray-800">{contact.name}</p>
                        <p className="text-xs text-gray-400">{contact.bank}</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => {
                        if (!isEnrolled) {
                          toast.error('Primero activa la seguridad biométrica');
                          return;
                        }
                        navigate('/transfer', { 
                          state: { 
                            prefilledContact: {
                              first_name: contact.first_name,
                              last_name: contact.last_name,
                              rut: contact.rut,
                              email: contact.email,
                              bank_name: contact.bank,
                              account_type: contact.account_type,
                              account_number: contact.account_number
                            }
                          } 
                        });
                      }}
                      className="px-3 py-1.5 text-xs font-medium text-[#1a365d] border border-[#1a365d]/30 rounded-lg opacity-0 group-hover:opacity-100 transition-all hover:bg-[#1a365d] hover:text-white"
                    >
                      Transferir
                    </button>
                  </div>
                ))}
              </div>
              
              <button className="w-full mt-4 flex items-center justify-center gap-2 text-sm text-[#1a365d] font-medium hover:underline">
                <Plus className="w-4 h-4" />
                Agregar favorito
              </button>
            </div>
          </section>

          {/* Acciones Rápidas */}
          <section className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 h-full">
              <h3 className="font-bold text-[#1a365d] mb-4">Acciones Rápidas</h3>
              <div className="space-y-3">
                <button 
                  onClick={() => isEnrolled ? navigate('/transfer') : toast.error('Primero activa la seguridad biométrica')}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="w-10 h-10 bg-[#f6ad55]/10 rounded-lg flex items-center justify-center">
                    <Send className="w-5 h-5 text-[#f6ad55]" />
                  </div>
                  <span className="font-medium text-gray-800">Nueva transferencia</span>
                </button>
                <button 
                  onClick={() => navigate('/profile')}
                  className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left"
                >
                  <div className="w-10 h-10 bg-[#1a365d]/10 rounded-lg flex items-center justify-center">
                    <User className="w-5 h-5 text-[#1a365d]" />
                  </div>
                  <span className="font-medium text-gray-800">Ver mi perfil</span>
                </button>
                {!isEnrolled && (
                  <button 
                    onClick={() => navigate('/enroll')}
                    className="w-full flex items-center gap-3 p-3 rounded-lg bg-[#f6ad55]/5 hover:bg-[#f6ad55]/10 transition-colors text-left border border-[#f6ad55]/20"
                  >
                    <div className="w-10 h-10 bg-[#f6ad55]/20 rounded-lg flex items-center justify-center">
                      <ShieldCheck className="w-5 h-5 text-[#f6ad55]" />
                    </div>
                    <span className="font-medium text-[#1a365d]">Activar biometría</span>
                  </button>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto px-6 py-6 text-center border-t border-gray-200 mt-8">
        <p className="text-gray-400 text-xs">
          © 2026 Banco Familia. Protegido con autenticación biométrica por voz.
        </p>
      </footer>
    </div>
  );
}
