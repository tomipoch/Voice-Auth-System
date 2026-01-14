import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, CreditCard, Shield, ShieldCheck, Mic, CheckCircle, Trash2, Lock, Edit } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import api from '../services/api';
import type { EnrollmentStatus } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';
import Header from '../components/Header';

export default function ProfilePage() {
  const navigate = useNavigate();
  const user = authService.getUser();
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
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
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [navigate]);

  const handleDeleteEnrollment = async () => {
    if (!confirm('¿Estás seguro de que deseas eliminar tu huella de voz? Deberás volver a registrarla para usar la verificación biométrica.')) {
      return;
    }

    setDeleting(true);
    try {
      await biometricService.deleteEnrollment();
      toast.success('Huella de voz eliminada correctamente');
      // Recargar estado
      const status = await biometricService.getEnrollmentStatus();
      setEnrollmentStatus(status);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Error al eliminar la huella de voz');
    } finally {
      setDeleting(false);
    }
  };

  const isEnrolled = enrollmentStatus?.is_enrolled || enrollmentStatus?.enrollment_status === 'enrolled';

  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      <Toaster position="top-right" />
      
      <Header showNav={true} isEnrolled={isEnrolled} />

      <main className="max-w-2xl mx-auto px-6 py-8">
        <h1 className="text-2xl font-bold text-[#1a365d] mb-8">Mi Perfil</h1>

        {/* User Info Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full bg-linear-to-br from-[#f6ad55] to-[#ed8936] flex items-center justify-center text-2xl font-bold text-[#1a365d]">
              {user?.first_name?.[0] || 'T'}
            </div>
            <div>
              <h2 className="text-xl font-bold text-[#1a365d]">{user?.first_name} {user?.last_name}</h2>
              <p className="text-gray-500 text-sm">Cliente Premium</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <Mail className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-400">Correo electrónico</p>
                <p className="font-medium text-gray-800">{user?.email || 'demo@banco.cl'}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <CreditCard className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-400">RUT</p>
                <p className="font-medium text-gray-800">{user?.rut || '12.345.678-9'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* PIN Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <Lock className="w-5 h-5 text-[#1a365d]" />
            <h3 className="font-bold text-[#1a365d]">PIN de Transferencias</h3>
          </div>

          {loading ? (
            <div className="py-4 text-center text-gray-500">Cargando...</div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  hasPin ? 'bg-[#48bb78]/20' : 'bg-orange-100'
                }`}>
                  {hasPin ? (
                    <ShieldCheck className="w-6 h-6 text-[#48bb78]" />
                  ) : (
                    <Lock className="w-6 h-6 text-orange-500" />
                  )}
                </div>
                <div>
                  <p className="font-medium text-gray-800">
                    {hasPin ? 'PIN configurado' : 'PIN no configurado'}
                  </p>
                  <p className="text-sm text-gray-500">
                    {hasPin 
                      ? 'Tu PIN de 6 dígitos está activo' 
                      : 'Necesitas configurar un PIN para transferir'
                    }
                  </p>
                </div>
              </div>
              
              <button
                onClick={() => navigate('/setup-pin')}
                className={`flex items-center gap-2 font-semibold px-4 py-2 rounded-lg transition-colors text-sm ${
                  hasPin 
                    ? 'text-[#1a365d] bg-gray-100 hover:bg-gray-200' 
                    : 'bg-orange-500 hover:bg-orange-600 text-white'
                }`}
              >
                <Edit className="w-4 h-4" />
                {hasPin ? 'Cambiar PIN' : 'Configurar PIN'}
              </button>
            </div>
          )}
        </div>

        {/* Security Card */}
        <div className={`rounded-xl shadow-sm border p-6 ${
          isEnrolled 
            ? 'bg-linear-to-br from-[#48bb78]/5 to-[#48bb78]/10 border-[#48bb78]/20' 
            : 'bg-white border-gray-100'
        }`}>
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-5 h-5 text-[#1a365d]" />
            <h3 className="font-bold text-[#1a365d]">Seguridad Biométrica</h3>
          </div>

          {loading ? (
            <div className="py-4 text-center text-gray-500">Cargando...</div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                    isEnrolled ? 'bg-[#48bb78]/20' : 'bg-gray-100'
                  }`}>
                    {isEnrolled ? (
                      <ShieldCheck className="w-6 h-6 text-[#48bb78]" />
                    ) : (
                      <Mic className="w-6 h-6 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-gray-800">
                      {isEnrolled ? 'Voz registrada' : 'Voz no registrada'}
                    </p>
                    <p className="text-sm text-gray-500">
                      {isEnrolled 
                        ? `${enrollmentStatus?.sample_count || 3} muestras de voz guardadas` 
                        : 'Registra tu voz para mayor seguridad'
                      }
                    </p>
                  </div>
                </div>
                
                {isEnrolled ? (
                  <div className="flex items-center gap-2 text-xs text-[#48bb78] font-bold uppercase bg-[#48bb78]/10 px-4 py-2 rounded-full">
                    <CheckCircle className="w-4 h-4" /> Activa
                  </div>
                ) : (
                  <button
                    onClick={() => navigate('/enroll')}
                    className="bg-[#f6ad55] hover:bg-[#ed8936] text-[#1a365d] font-semibold px-4 py-2 rounded-lg transition-colors text-sm"
                  >
                    Registrar voz
                  </button>
                )}
              </div>

              {isEnrolled && (
                <div className="pt-4 border-t border-gray-200">
                  <button
                    onClick={handleDeleteEnrollment}
                    disabled={deleting}
                    className="flex items-center gap-2 text-red-600 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    {deleting ? 'Eliminando...' : 'Eliminar huella de voz'}
                  </button>
                  <p className="text-xs text-gray-500 mt-2">
                    Al eliminar tu huella de voz, deberás volver a registrarla para usar la verificación biométrica en transferencias.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
