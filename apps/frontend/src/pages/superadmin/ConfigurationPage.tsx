import { useState, useEffect } from 'react';
import {
  RefreshCw,
  Loader2,
  Save,
  Shield,
  Lock,
  AlertTriangle,
} from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import toast from 'react-hot-toast';

interface SecurityConfig {
  max_login_attempts: number;
  lockout_duration_minutes: number;
  session_timeout_minutes: number;
  require_2fa_admins: boolean;
  min_password_length: number;
  password_expiry_days: number;
}

interface VerificationConfig {
  speaker_threshold: number;
  antispoofing_threshold: number;
  text_similarity_threshold: number;
  max_retries: number;
  challenge_expiry_seconds: number;
}

const ConfigurationPage = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [securityConfig, setSecurityConfig] = useState<SecurityConfig>({
    max_login_attempts: 5,
    lockout_duration_minutes: 15,
    session_timeout_minutes: 120,
    require_2fa_admins: false,
    min_password_length: 8,
    password_expiry_days: 90,
  });

  const [verificationConfig, setVerificationConfig] = useState<VerificationConfig>({
    speaker_threshold: 0.65,
    antispoofing_threshold: 0.5,
    text_similarity_threshold: 0.8,
    max_retries: 3,
    challenge_expiry_seconds: 300,
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      // Load current values - mock for now
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (error) {
      console.error('Error loading config:', error);
      toast.error('Error al cargar configuración');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      toast.success('Configuración guardada');
    } catch {
      toast.error('Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  const InputField = ({
    label,
    value,
    onChange,
    type = 'number',
    min,
    max,
    step,
    suffix,
  }: {
    label: string;
    value: number;
    onChange: (v: number) => void;
    type?: string;
    min?: number;
    max?: number;
    step?: number;
    suffix?: string;
  }) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="w-full px-3 py-3 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800"
        />
        {suffix && <span className="text-sm text-gray-500 whitespace-nowrap">{suffix}</span>}
      </div>
    </div>
  );

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-linear-to-r from-gray-800 via-purple-700 to-indigo-800 dark:from-gray-200 dark:via-purple-400 dark:to-indigo-400 bg-clip-text text-transparent mb-2">
              Configuración del Sistema
            </h1>
            <p className="text-lg text-purple-600/80 dark:text-purple-400/80 font-medium">
              Umbrales y políticas de seguridad
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={loadConfig}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
              Guardar Cambios
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Verification Thresholds */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/30">
              <Shield className="h-5 w-5 text-blue-600" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Umbrales de Verificación
            </h3>
          </div>

          <div className="space-y-4">
            <div className="bg-gray-50 dark:bg-gray-800/50 p-4 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Umbral de Speaker Recognition
                </label>
                <span className={`text-sm font-bold px-2 py-1 rounded ${
                  verificationConfig.speaker_threshold >= 0.7 
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' 
                    : verificationConfig.speaker_threshold >= 0.55 
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' 
                      : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                }`}>
                  {verificationConfig.speaker_threshold.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={verificationConfig.speaker_threshold}
                onChange={(e) =>
                  setVerificationConfig({ ...verificationConfig, speaker_threshold: Number(e.target.value) })
                }
                className="w-full accent-purple-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>🟢 Menos estricto</span>
                <span>🔴 Más estricto</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Umbral Anti-Spoofing: {verificationConfig.antispoofing_threshold}
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={verificationConfig.antispoofing_threshold}
                onChange={(e) =>
                  setVerificationConfig({ ...verificationConfig, antispoofing_threshold: Number(e.target.value) })
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Umbral Similitud de Texto: {verificationConfig.text_similarity_threshold}
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={verificationConfig.text_similarity_threshold}
                onChange={(e) =>
                  setVerificationConfig({ ...verificationConfig, text_similarity_threshold: Number(e.target.value) })
                }
                className="w-full"
              />
            </div>

            <InputField
              label="Máximo de Reintentos"
              value={verificationConfig.max_retries}
              onChange={(v) => setVerificationConfig({ ...verificationConfig, max_retries: v })}
              min={1}
              max={10}
            />

            <InputField
              label="Expiración de Challenge"
              value={verificationConfig.challenge_expiry_seconds}
              onChange={(v) => setVerificationConfig({ ...verificationConfig, challenge_expiry_seconds: v })}
              min={60}
              max={600}
              suffix="segundos"
            />
          </div>
        </Card>

        {/* Security Policies */}
        <Card className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900/30">
              <Lock className="h-5 w-5 text-red-600" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Políticas de Seguridad
            </h3>
          </div>

          <div className="space-y-4">
            <InputField
              label="Intentos de Login Máximos"
              value={securityConfig.max_login_attempts}
              onChange={(v) => setSecurityConfig({ ...securityConfig, max_login_attempts: v })}
              min={3}
              max={10}
            />

            <InputField
              label="Duración de Bloqueo"
              value={securityConfig.lockout_duration_minutes}
              onChange={(v) => setSecurityConfig({ ...securityConfig, lockout_duration_minutes: v })}
              min={5}
              max={60}
              suffix="minutos"
            />

            <InputField
              label="Timeout de Sesión"
              value={securityConfig.session_timeout_minutes}
              onChange={(v) => setSecurityConfig({ ...securityConfig, session_timeout_minutes: v })}
              min={15}
              max={480}
              suffix="minutos"
            />

            <InputField
              label="Longitud Mínima de Contraseña"
              value={securityConfig.min_password_length}
              onChange={(v) => setSecurityConfig({ ...securityConfig, min_password_length: v })}
              min={6}
              max={20}
              suffix="caracteres"
            />

            <InputField
              label="Expiración de Contraseña"
              value={securityConfig.password_expiry_days}
              onChange={(v) => setSecurityConfig({ ...securityConfig, password_expiry_days: v })}
              min={0}
              max={365}
              suffix="días (0=nunca)"
            />

            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">2FA para Admins</p>
                <p className="text-xs text-gray-500">Requerir autenticación de dos factores</p>
              </div>
              <button
                onClick={() =>
                  setSecurityConfig({ ...securityConfig, require_2fa_admins: !securityConfig.require_2fa_admins })
                }
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  securityConfig.require_2fa_admins ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                }`}
              >
                <span
                  className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                    securityConfig.require_2fa_admins ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </Card>
      </div>

      {/* Warning */}
      <Card className="p-4 mt-6 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-700">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
              Cambios de configuración
            </p>
            <p className="text-xs text-yellow-600 dark:text-yellow-300 mt-1">
              Los cambios en los umbrales y políticas afectarán a todas las verificaciones futuras. Los umbrales más estrictos pueden aumentar los falsos rechazos.
            </p>
          </div>
        </div>
      </Card>
    </MainLayout>
  );
};

export default ConfigurationPage;
