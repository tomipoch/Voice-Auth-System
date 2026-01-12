import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Send, User, ArrowLeft, AlertTriangle, CheckCircle, Shield, 
  UserPlus, Users, Mic, Loader2, Hash, DollarSign 
} from 'lucide-react';
import authService from '../services/authService';
import biometricService from '../services/biometricService';
import api from '../services/api';
import type { EnrollmentStatus } from '../services/biometricService';
import toast, { Toaster } from 'react-hot-toast';
import Header from '../components/Header';

interface Contact {
  id: number;
  first_name: string;
  last_name: string;
  rut: string;
  email: string;
  bank_name: string;
  account_type: string;
  account_number: string;
  is_favorite: number;
}

type Step = 'select-type' | 'select-contact' | 'form' | 'pin' | 'voice-verification' | 'success';

export default function TransferPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('select-type');
  const [enrollmentStatus, setEnrollmentStatus] = useState<EnrollmentStatus | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(false);
  const [verificationId, setVerificationId] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    recipient_first_name: '',
    recipient_last_name: '',
    recipient_rut: '',
    recipient_email: '',
    recipient_bank: 'Banco Pirulete',
    recipient_account_type: 'Cuenta Corriente',
    recipient_account_number: '',
    amount: '',
    description: '',
    save_contact: false,
  });
  
  const [pin, setPin] = useState('');
  const [requiresVoice, setRequiresVoice] = useState(false);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/');
      return;
    }
    
    const loadData = async () => {
      try {
        const [status, contactsList] = await Promise.all([
          biometricService.getEnrollmentStatus(),
          api.get('/api/contacts').then(res => res.data).catch(() => [])
        ]);
        setEnrollmentStatus(status);
        setContacts(contactsList);
      } catch (error) {
        console.error('Error loading data:', error);
      }
    };
    loadData();
  }, [navigate]);

  const isEnrolled = enrollmentStatus?.is_enrolled || enrollmentStatus?.enrollment_status === 'enrolled';
  const amount = parseFloat(formData.amount) || 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const handleSelectType = (type: 'new' | 'saved') => {
    if (type === 'new') {
      setStep('form');
    } else {
      setStep('select-contact');
    }
  };

  const handleSelectContact = (contact: Contact) => {
    setSelectedContact(contact);
    setFormData(prev => ({
      ...prev,
      recipient_first_name: contact.first_name,
      recipient_last_name: contact.last_name,
      recipient_rut: contact.rut,
      recipient_email: contact.email,
      recipient_bank: contact.bank_name,
      recipient_account_type: contact.account_type,
      recipient_account_number: contact.account_number,
    }));
    setStep('form');
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.recipient_first_name || !formData.recipient_last_name || !formData.recipient_rut || 
        !formData.recipient_email || !formData.recipient_account_number || !formData.amount) {
      toast.error('Completa todos los campos obligatorios');
      return;
    }

    if (amount <= 0) {
      toast.error('El monto debe ser mayor a $0');
      return;
    }

    if (amount > 200000 && !isEnrolled) {
      toast.error('Debes activar la verificación por voz para transferencias mayores a $200,000');
      setTimeout(() => navigate('/enroll'), 2000);
      return;
    }

    setStep('pin');
  };

  const handlePinSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (pin.length !== 6) {
      toast.error('El PIN debe tener 6 dígitos');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post('/api/transfers/validate', {
        amount,
        recipient_first_name: formData.recipient_first_name,
        recipient_last_name: formData.recipient_last_name,
        recipient_rut: formData.recipient_rut,
        recipient_email: formData.recipient_email,
        recipient_account_number: formData.recipient_account_number,
        recipient_account_type: formData.recipient_account_type,
        recipient_bank: formData.recipient_bank,
        pin,
      });

      if (response.data.requires_voice_verification) {
        setRequiresVoice(true);
        setStep('voice-verification');
      } else {
        await executeTransfer();
      }
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al validar PIN');
    } finally {
      setLoading(false);
    }
  };

  const executeTransfer = async (voiceVerificationId?: string) => {
    setLoading(true);
    try {
      const response = await api.post('/api/transfers/execute', {
        amount,
        recipient_first_name: formData.recipient_first_name,
        recipient_last_name: formData.recipient_last_name,
        recipient_rut: formData.recipient_rut,
        recipient_email: formData.recipient_email,
        recipient_account_number: formData.recipient_account_number,
        recipient_account_type: formData.recipient_account_type,
        recipient_bank: formData.recipient_bank,
        description: formData.description,
        pin,
        verification_id: voiceVerificationId || null,
        save_contact: formData.save_contact && !selectedContact,
      });

      setStep('success');
      toast.success('¡Transferencia exitosa!');
    } catch (error: any) {
      toast.error(error.response?.data?.error || 'Error al realizar la transferencia');
    } finally {
      setLoading(false);
    }
  };

  const renderSelectType = () => (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => navigate('/dashboard')}
        className="flex items-center gap-2 text-[#1a365d] hover:text-[#2c5282] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Volver al Dashboard
      </button>

      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a365d]/10 rounded-2xl mb-4">
          <Send className="w-8 h-8 text-[#1a365d]" />
        </div>
        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Nueva Transferencia</h1>
        <p className="text-gray-600">Selecciona cómo quieres transferir</p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <button
          onClick={() => handleSelectType('saved')}
          className="bg-white border-2 border-gray-200 hover:border-[#1a365d] rounded-2xl p-8 text-center transition-all group"
        >
          <Users className="w-12 h-12 text-[#1a365d] mx-auto mb-4 group-hover:scale-110 transition-transform" />
          <h3 className="text-lg font-bold text-[#1a365d] mb-2">Contacto Guardado</h3>
          <p className="text-sm text-gray-600">Transferir a un contacto de tu lista</p>
          {contacts.length > 0 && (
            <span className="inline-block mt-3 px-3 py-1 bg-[#48bb78]/10 text-[#48bb78] text-xs font-semibold rounded-full">
              {contacts.length} contacto{contacts.length !== 1 ? 's' : ''}
            </span>
          )}
        </button>

        <button
          onClick={() => handleSelectType('new')}
          className="bg-white border-2 border-gray-200 hover:border-[#1a365d] rounded-2xl p-8 text-center transition-all group"
        >
          <UserPlus className="w-12 h-12 text-[#1a365d] mx-auto mb-4 group-hover:scale-110 transition-transform" />
          <h3 className="text-lg font-bold text-[#1a365d] mb-2">Nuevo Contacto</h3>
          <p className="text-sm text-gray-600">Ingresar datos de cuenta manualmente</p>
        </button>
      </div>
    </div>
  );

  const renderSelectContact = () => (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => setStep('select-type')}
        className="flex items-center gap-2 text-[#1a365d] hover:text-[#2c5282] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Volver
      </button>

      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Selecciona un Contacto</h1>
        <p className="text-gray-600">Tus contactos guardados</p>
      </div>

      {contacts.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 p-8 text-center">
          <Users className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No tienes contactos guardados</p>
          <button
            onClick={() => handleSelectType('new')}
            className="mt-4 text-[#1a365d] hover:text-[#2c5282] font-semibold"
          >
            Agregar nuevo contacto
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {contacts.map(contact => (
            <button
              key={contact.id}
              onClick={() => handleSelectContact(contact)}
              className="w-full bg-white border border-gray-200 hover:border-[#1a365d] rounded-xl p-4 text-left transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-[#1a365d]/10 flex items-center justify-center">
                  <User className="w-6 h-6 text-[#1a365d]" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-[#1a365d] group-hover:text-[#2c5282]">
                    {contact.first_name} {contact.last_name}
                  </h3>
                  <p className="text-sm text-gray-600">{contact.bank_name} - {contact.account_type}</p>
                  <p className="text-sm text-gray-500">RUT: {contact.rut}</p>
                </div>
                {contact.is_favorite === 1 && (
                  <span className="text-yellow-500">★</span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );

  const renderForm = () => (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => setStep(selectedContact ? 'select-contact' : 'select-type')}
        className="flex items-center gap-2 text-[#1a365d] hover:text-[#2c5282] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Volver
      </button>

      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Datos de la Transferencia</h1>
        <p className="text-gray-600">Completa la información</p>
      </div>

      <form onSubmit={handleFormSubmit} className="bg-white rounded-2xl border border-gray-100 p-6 space-y-6">
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-[#1a365d] mb-2">
              Nombre *
            </label>
            <input
              type="text"
              value={formData.recipient_first_name}
              onChange={(e) => setFormData({ ...formData, recipient_first_name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
              placeholder="Juan"
              disabled={!!selectedContact}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-[#1a365d] mb-2">
              Apellido *
            </label>
            <input
              type="text"
              value={formData.recipient_last_name}
              onChange={(e) => setFormData({ ...formData, recipient_last_name: e.target.value })}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
              placeholder="Pérez"
              disabled={!!selectedContact}
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            RUT *
          </label>
          <input
            type="text"
            value={formData.recipient_rut}
            onChange={(e) => setFormData({ ...formData, recipient_rut: e.target.value })}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
            placeholder="12.345.678-9"
            disabled={!!selectedContact}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            Correo electrónico *
          </label>
          <input
            type="email"
            value={formData.recipient_email}
            onChange={(e) => setFormData({ ...formData, recipient_email: e.target.value })}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
            placeholder="juan.perez@example.com"
            disabled={!!selectedContact}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            Banco *
          </label>
          <select
            value={formData.recipient_bank}
            onChange={(e) => setFormData({ ...formData, recipient_bank: e.target.value })}
            className="w-full px-4 py-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent text-base"
            disabled={!!selectedContact}
            required
          >
            <option value="Banco Pirulete">Banco Pirulete</option>
            <option value="Banco Estado">Banco Estado</option>
            <option value="Banco Chile">Banco Chile</option>
            <option value="Banco Santander">Banco Santander</option>
            <option value="Banco Falabella">Banco Falabella</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            Tipo de cuenta *
          </label>
          <select
            value={formData.recipient_account_type}
            onChange={(e) => setFormData({ ...formData, recipient_account_type: e.target.value })}
            className="w-full px-4 py-4 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent text-base"
            disabled={!!selectedContact}
            required
          >
            <option value="Cuenta Corriente">Cuenta Corriente</option>
            <option value="Cuenta Vista">Cuenta Vista</option>
            <option value="Cuenta de Ahorro">Cuenta de Ahorro</option>
            <option value="Cuenta RUT">Cuenta RUT</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            Número de cuenta *
          </label>
          <input
            type="text"
            value={formData.recipient_account_number}
            onChange={(e) => setFormData({ ...formData, recipient_account_number: e.target.value })}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
            placeholder="1234567890"
            disabled={!!selectedContact}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            Monto a transferir *
          </label>
          <div className="relative">
            <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="number"
              value={formData.amount}
              onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
              className="w-full pl-12 pr-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
              placeholder="0"
              min="1"
              required
            />
          </div>
          {amount > 0 && (
            <p className="mt-2 text-sm text-gray-600">
              {formatCurrency(amount)}
            </p>
          )}
        </div>

        {amount > 200000 && (
          <div className="bg-[#f6ad55]/10 border-l-4 border-[#f6ad55] rounded-r-lg p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-[#f6ad55] flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-[#1a365d]">Verificación por voz requerida</p>
              <p className="text-sm text-gray-600 mt-1">
                Las transferencias mayores a $200,000 requieren verificación por voz por seguridad.
              </p>
              {!isEnrolled && (
                <button
                  type="button"
                  onClick={() => navigate('/enroll')}
                  className="mt-2 text-sm text-[#f6ad55] hover:text-[#ed8936] font-semibold"
                >
                  Activar verificación por voz →
                </button>
              )}
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-[#1a365d] mb-2">
            Descripción (opcional)
          </label>
          <input
            type="text"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
            placeholder="Pago de servicios"
          />
        </div>

        {!selectedContact && (
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={formData.save_contact}
              onChange={(e) => setFormData({ ...formData, save_contact: e.target.checked })}
              className="w-5 h-5 text-[#1a365d] border-gray-300 rounded focus:ring-[#1a365d]"
            />
            <span className="text-sm text-gray-700">Guardar como contacto</span>
          </label>
        )}

        <button
          type="submit"
          className="w-full bg-[#1a365d] hover:bg-[#2c5282] text-white font-semibold py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          Continuar
          <ArrowLeft className="w-5 h-5 rotate-180" />
        </button>
      </form>
    </div>
  );

  const renderPinStep = () => (
    <div className="max-w-md mx-auto">
      <button
        onClick={() => setStep('form')}
        className="flex items-center gap-2 text-[#1a365d] hover:text-[#2c5282] mb-6 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Volver
      </button>

      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-[#1a365d]/10 rounded-2xl mb-4">
          <Hash className="w-8 h-8 text-[#1a365d]" />
        </div>
        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Ingresa tu PIN</h1>
        <p className="text-gray-600">PIN de 6 dígitos para transferencias</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6">
        <div className="space-y-3 mb-6">
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Beneficiario:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_first_name} {formData.recipient_last_name}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">RUT:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_rut}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Cuenta:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_account_number}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Banco:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_bank}</span>
          </div>
          <div className="flex justify-between py-2 border-t pt-3">
            <span className="text-gray-600">Monto:</span>
            <span className="text-xl font-bold text-[#1a365d]">{formatCurrency(amount)}</span>
          </div>
        </div>

        <form onSubmit={handlePinSubmit} className="space-y-4">
          <div>
            <input
              type="password"
              value={pin}
              onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl text-center text-2xl font-mono tracking-widest focus:outline-none focus:ring-2 focus:ring-[#1a365d] focus:border-transparent"
              placeholder="••••••"
              maxLength={6}
              pattern="[0-9]{6}"
              required
            />
            <p className="text-xs text-gray-500 text-center mt-2">
              PIN demo: 123456 (demo@banco.cl) | 654321 (juan@banco.cl)
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || pin.length !== 6}
            className="w-full bg-[#1a365d] hover:bg-[#2c5282] disabled:bg-gray-300 text-white font-semibold py-3 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Validando...
              </>
            ) : (
              <>
                Confirmar Transferencia
                <CheckCircle className="w-5 h-5" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );

  const renderVoiceVerification = () => (
    <div className="max-w-md mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-[#f6ad55]/10 rounded-2xl mb-4">
          <Shield className="w-8 h-8 text-[#f6ad55]" />
        </div>
        <h1 className="text-2xl font-bold text-[#1a365d] mb-2">Verificación por Voz</h1>
        <p className="text-gray-600">Verifica tu identidad con tu voz</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 p-6 text-center">
        <p className="text-gray-700 mb-6">
          Por tu seguridad, esta transferencia requiere verificación por voz.
        </p>

        <div className="bg-[#f6ad55]/10 rounded-xl p-6 mb-6">
          <p className="text-2xl font-bold text-[#1a365d] mb-2">{formatCurrency(amount)}</p>
          <p className="text-sm text-gray-600">a {formData.recipient_first_name} {formData.recipient_last_name}</p>
        </div>

        <button
          onClick={() => {
            toast.success('Verificación por voz completada');
            executeTransfer('voice-' + Date.now());
          }}
          disabled={loading}
          className="w-full bg-[#f6ad55] hover:bg-[#ed8936] disabled:bg-gray-300 text-[#1a365d] font-semibold py-4 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Procesando...
            </>
          ) : (
            <>
              <Mic className="w-6 h-6" />
              Verificar con mi voz
            </>
          )}
        </button>
      </div>
    </div>
  );

  const renderSuccess = () => (
    <div className="max-w-md mx-auto text-center">
      <div className="inline-flex items-center justify-center w-20 h-20 bg-[#48bb78]/10 rounded-full mb-6">
        <CheckCircle className="w-12 h-12 text-[#48bb78]" />
      </div>

      <h1 className="text-2xl font-bold text-[#1a365d] mb-2">¡Transferencia Exitosa!</h1>
      <p className="text-gray-600 mb-8">Tu dinero ha sido enviado</p>

      <div className="bg-white rounded-2xl border border-gray-100 p-6 mb-6 text-left">
        <div className="space-y-3">
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Beneficiario:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_first_name} {formData.recipient_last_name}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">RUT:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_rut}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Banco:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_bank}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Tipo cuenta:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_account_type}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-600">Cuenta:</span>
            <span className="font-semibold text-[#1a365d]">{formData.recipient_account_number}</span>
          </div>
          <div className="flex justify-between py-2 border-t pt-3">
            <span className="text-gray-600">Monto:</span>
            <span className="text-xl font-bold text-[#48bb78]">-{formatCurrency(amount)}</span>
          </div>
          {requiresVoice && (
            <div className="flex items-center gap-2 py-2 text-sm text-[#f6ad55]">
              <Shield className="w-4 h-4" />
              <span>Verificado con voz</span>
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        <button
          onClick={() => navigate('/dashboard')}
          className="w-full bg-[#1a365d] hover:bg-[#2c5282] text-white font-semibold py-3 px-6 rounded-xl transition-colors"
        >
          Volver al Dashboard
        </button>
        
        <button
          onClick={() => {
            setStep('select-type');
            setSelectedContact(null);
            setFormData({
              recipient_first_name: '',
              recipient_last_name: '',
              recipient_rut: '',
              recipient_email: '',
              recipient_bank: 'Banco Pirulete',
              recipient_account_type: 'Cuenta Corriente',
              recipient_account_number: '',
              amount: '',
              description: '',
              save_contact: false,
            });
            setPin('');
            setRequiresVoice(false);
            setVerificationId(null);
          }}
          className="w-full bg-white hover:bg-gray-50 text-[#1a365d] font-semibold py-3 px-6 rounded-xl border-2 border-[#1a365d] transition-colors"
        >
          Nueva Transferencia
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      <Toaster position="top-right" />
      <Header showNav={true} isEnrolled={isEnrolled} />

      <main className="max-w-7xl mx-auto px-6 py-12">
        {step === 'select-type' && renderSelectType()}
        {step === 'select-contact' && renderSelectContact()}
        {step === 'form' && renderForm()}
        {step === 'pin' && renderPinStep()}
        {step === 'voice-verification' && renderVoiceVerification()}
        {step === 'success' && renderSuccess()}
      </main>
    </div>
  );
}
