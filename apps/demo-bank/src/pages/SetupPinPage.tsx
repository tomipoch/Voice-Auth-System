import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, ArrowLeft, Eye, EyeOff } from 'lucide-react';
import api from '../services/api';
import toast, { Toaster } from 'react-hot-toast';
import Header from '../components/Header';
import authService from '../services/authService';

export default function SetupPinPage() {
  const navigate = useNavigate();
  const [hasExistingPin, setHasExistingPin] = useState(false);
  const [currentPin, setCurrentPin] = useState('');
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [showPin, setShowPin] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checkingPin, setCheckingPin] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }

    const checkPinStatus = async () => {
      try {
        const response = await api.get('/pin/status');
        setHasExistingPin(response.data.has_pin);
      } catch (error) {
        console.error('Error checking PIN status:', error);
      } finally {
        setCheckingPin(false);
      }
    };

    checkPinStatus();
  }, [navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (hasExistingPin && currentPin.length !== 6) {
      toast.error('Ingresa tu PIN actual de 6 dígitos');
      return;
    }

    if (pin.length !== 6) {
      toast.error('El PIN debe tener exactamente 6 dígitos');
      return;
    }

    if (pin !== confirmPin) {
      toast.error('Los PINs no coinciden');
      return;
    }

    if (!/^\d{6}$/.test(pin)) {
      toast.error('El PIN debe contener solo números');
      return;
    }

    setLoading(true);
    try {
      await api.post('/pin/set', { 
        pin,
        current_pin: hasExistingPin ? currentPin : undefined
      });
      toast.success(hasExistingPin ? '¡PIN actualizado exitosamente!' : '¡PIN configurado exitosamente!');
      setTimeout(() => navigate('/profile'), 1500);
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al configurar el PIN');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a365d] via-[#2c5282] to-[#1a365d]">
      <Toaster position="top-center" />
      <Header />
      
      <div className="max-w-md mx-auto px-4 py-12">
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-2 text-white/80 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Volver al Dashboard
        </button>

        <div className="bg-white rounded-3xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a365d]/10 rounded-2xl mb-4">
              <Lock className="w-8 h-8 text-[#1a365d]" />
            </div>
            <h1 className="text-2xl font-bold text-[#1a365d] mb-2">
              {hasExistingPin ? 'Cambiar PIN de Transferencias' : 'Configura tu PIN de Transferencias'}
            </h1>
            <p className="text-gray-600">
              {hasExistingPin 
                ? 'Actualiza tu PIN de 6 dígitos para autorizar transferencias'
                : 'Crea un PIN de 6 dígitos para autorizar tus transferencias'
              }
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {hasExistingPin && (
              <div>
                <label className="block text-sm font-semibold text-[#1a365d] mb-2">
                  PIN Actual *
                </label>
                <input
                  type={showPin ? 'text' : 'password'}
                  value={currentPin}
                  onChange={(e) => setCurrentPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent text-center text-2xl tracking-widest font-mono"
                  placeholder="••••••"
                  maxLength={6}
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-[#1a365d] mb-2">
                {hasExistingPin ? 'Nuevo PIN (6 dígitos) *' : 'PIN (6 dígitos) *'}
              </label>
              <div className="relative">
                <input
                  type={showPin ? 'text' : 'password'}
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full px-4 py-3 pr-12 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent text-center text-2xl tracking-widest font-mono"
                  placeholder="••••••"
                  maxLength={6}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPin(!showPin)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPin ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">Solo números del 0-9</p>
            </div>

            <div>
              <label className="block text-sm font-semibold text-[#1a365d] mb-2">
                Confirmar PIN *
              </label>
              <input
                type={showPin ? 'text' : 'password'}
                value={confirmPin}
                onChange={(e) => setConfirmPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent text-center text-2xl tracking-widest font-mono"
                placeholder="••••••"
                maxLength={6}
                required
              />
            </div>

            {pin && confirmPin && pin !== confirmPin && (
              <div className="bg-red-50 border-l-4 border-red-500 p-3 rounded-r-lg">
                <p className="text-sm text-red-700">Los PINs no coinciden</p>
              </div>
            )}

            {pin && confirmPin && pin === confirmPin && pin.length === 6 && (
              <div className="bg-green-50 border-l-4 border-green-500 p-3 rounded-r-lg">
                <p className="text-sm text-green-700">✓ Los PINs coinciden</p>
              </div>
            )}

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg">
              <h3 className="font-semibold text-[#1a365d] text-sm mb-1">
                Consejos de seguridad
              </h3>
              <ul className="text-xs text-gray-600 space-y-1">
                <li>• No uses fechas de nacimiento o números consecutivos</li>
                <li>• No compartas tu PIN con nadie</li>
                <li>• Memoriza tu PIN, no lo guardes por escrito</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={loading || pin.length !== 6 || pin !== confirmPin}
              className="w-full bg-[#1a365d] text-white py-3 rounded-xl font-semibold hover:bg-[#2c5282] transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Configurando...
                </>
              ) : (
                <>
                  <Lock className="w-5 h-5" />
                  Configurar PIN
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
