import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mic, Shield, CheckCircle, XCircle } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const VerificationPage = () => {
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [phrase] = useState("Mi voz es mi contraseña, úsala para verificar mi identidad");

  const handleStartVerification = () => {
    setIsVerifying(true);
    setVerificationResult(null);
    
    // Simular proceso de verificación
    setTimeout(() => {
      setIsVerifying(false);
      // Simular resultado (en producción esto vendrá del backend)
      setVerificationResult({
        success: Math.random() > 0.3, // 70% de éxito para demo
        confidence: Math.random() * 0.4 + 0.6, // Entre 60% y 100%
      });
    }, 3000);
  };

  const resetVerification = () => {
    setVerificationResult(null);
    setIsVerifying(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Link 
            to="/dashboard" 
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Volver al Dashboard
          </Link>
        </div>

        {/* Título */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Verificación de Identidad por Voz
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Verifica tu identidad usando tu voz. Este proceso es rápido y seguro.
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Verification Panel */}
          <div className="lg:col-span-2">
            <Card className="p-8">
              <div className="text-center">
                {!verificationResult ? (
                  <>
                    <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 ${
                      isVerifying 
                        ? 'bg-blue-100 animate-pulse' 
                        : 'bg-green-100'
                    }`}>
                      <Shield className={`h-12 w-12 ${
                        isVerifying ? 'text-blue-600' : 'text-green-600'
                      }`} />
                    </div>
                    
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      {isVerifying ? 'Verificando...' : 'Listo para Verificar'}
                    </h2>
                    
                    {!isVerifying && (
                      <>
                        <p className="text-gray-600 mb-8">
                          Presiona el botón y di la siguiente frase:
                        </p>

                        <Card className="bg-blue-50 border-blue-200 mb-8 p-6">
                          <p className="text-lg font-medium text-blue-900">
                            "{phrase}"
                          </p>
                        </Card>

                        <Button 
                          size="lg" 
                          className="px-8"
                          onClick={handleStartVerification}
                        >
                          <Mic className="h-5 w-5 mr-2" />
                          Iniciar Verificación
                        </Button>
                      </>
                    )}

                    {isVerifying && (
                      <div className="space-y-4">
                        <div className="flex justify-center">
                          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                        <p className="text-gray-600">
                          Analizando tu voz...
                        </p>
                        <div className="bg-gray-100 rounded-full h-2 max-w-xs mx-auto">
                          <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  // Resultado de verificación
                  <>
                    <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 ${
                      verificationResult.success 
                        ? 'bg-green-100' 
                        : 'bg-red-100'
                    }`}>
                      {verificationResult.success ? (
                        <CheckCircle className="h-12 w-12 text-green-600" />
                      ) : (
                        <XCircle className="h-12 w-12 text-red-600" />
                      )}
                    </div>
                    
                    <h2 className={`text-2xl font-bold mb-4 ${
                      verificationResult.success 
                        ? 'text-green-900' 
                        : 'text-red-900'
                    }`}>
                      {verificationResult.success 
                        ? '¡Verificación Exitosa!' 
                        : 'Verificación Fallida'}
                    </h2>
                    
                    <p className={`mb-6 ${
                      verificationResult.success 
                        ? 'text-green-700' 
                        : 'text-red-700'
                    }`}>
                      {verificationResult.success 
                        ? 'Tu identidad ha sido verificada correctamente.'
                        : 'No se pudo verificar tu identidad. Inténtalo nuevamente.'}
                    </p>

                    <div className="mb-6">
                      <p className="text-sm text-gray-600 mb-2">
                        Nivel de confianza:
                      </p>
                      <div className="bg-gray-200 rounded-full h-3 max-w-xs mx-auto">
                        <div 
                          className={`h-3 rounded-full ${
                            verificationResult.success ? 'bg-green-500' : 'bg-red-500'
                          }`}
                          style={{width: `${verificationResult.confidence * 100}%`}}
                        ></div>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {(verificationResult.confidence * 100).toFixed(1)}%
                      </p>
                    </div>

                    <div className="flex space-x-4 justify-center">
                      <Button 
                        variant="secondary"
                        onClick={resetVerification}
                      >
                        Intentar Nuevamente
                      </Button>
                      <Link to="/dashboard">
                        <Button variant="primary">
                          Volver al Dashboard
                        </Button>
                      </Link>
                    </div>
                  </>
                )}
              </div>
            </Card>
          </div>

          {/* Info Panel */}
          <div className="space-y-6">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Proceso de Verificación
              </h3>
              <div className="space-y-4 text-sm text-gray-600">
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-blue-600 text-xs font-semibold">1</span>
                  </div>
                  <p>Graba la frase proporcionada</p>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-blue-600 text-xs font-semibold">2</span>
                  </div>
                  <p>El sistema analiza tu patrón vocal</p>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-blue-600 text-xs font-semibold">3</span>
                  </div>
                  <p>Se compara con tu perfil registrado</p>
                </div>
                <div className="flex items-start">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                    <span className="text-blue-600 text-xs font-semibold">4</span>
                  </div>
                  <p>Recibes el resultado de la verificación</p>
                </div>
              </div>
            </Card>

            <Card className="p-6 bg-blue-50 border-blue-200">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">
                Consejos
              </h3>
              <ul className="text-sm text-blue-700 space-y-2">
                <li>• Habla claramente y a velocidad normal</li>
                <li>• Usa un ambiente silencioso</li>
                <li>• Mantén la misma distancia del micrófono</li>
                <li>• Si falla, espera un momento e inténtalo de nuevo</li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerificationPage;