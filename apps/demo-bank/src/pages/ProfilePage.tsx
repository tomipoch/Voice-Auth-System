import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Mail, CreditCard, Shield, ShieldCheck, Mic, CheckCircle } from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import type { EnrollmentStatus } from '../services/biometricService';
import { Toaster } from 'react-hot-toast';
import Header from '../components/Header';

export default function ProfilePage() {
  const navigate = useNavigate();
  const user = authService.getUser();
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    };
    
    loadStatus();
  }, [navigate]);

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
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#f6ad55] to-[#ed8936] flex items-center justify-center text-2xl font-bold text-[#1a365d]">
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

        {/* Security Card */}
        <div className={`rounded-xl shadow-sm border p-6 ${
          isEnrolled 
            ? 'bg-gradient-to-br from-[#48bb78]/5 to-[#48bb78]/10 border-[#48bb78]/20' 
            : 'bg-white border-gray-100'
        }`}>
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-5 h-5 text-[#1a365d]" />
            <h3 className="font-bold text-[#1a365d]">Seguridad Biométrica</h3>
          </div>

          {loading ? (
            <div className="py-4 text-center text-gray-500">Cargando...</div>
          ) : (
            <div className="flex items-center justify-between">
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
          )}
        </div>
      </main>
    </div>
  );
}
