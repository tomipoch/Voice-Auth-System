import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mic, Shield, CheckCircle, XCircle } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import MainLayout from '../components/ui/MainLayout';

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
    <MainLayout>
      {/* Header */}
      <div className="flex items-center mb-8">
        <Link 
          to="/dashboard" 
          className="flex items-center px-4 py-2 text-blue-600 hover:text-blue-700 transition-all duration-300 bg-white dark:bg-gray-900/70 backdrop-blur-xl border border-blue-200/40 rounded-xl hover:bg-white dark:bg-gray-900/80 hover:shadow-md"
        >
          <ArrowLeft className="h-5 w-5 mr-2" />
          Volver al Dashboard
        </Link>
      </div>

      {/* Título */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-green-800 bg-clip-text text-transparent mb-4">
          Verificación de Identidad por Voz
        </h1>
        <p className="text-lg text-blue-600/80 font-medium max-w-2xl mx-auto">
          Verifica tu identidad usando tu voz. Este proceso es rápido y seguro.
        </p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Verification Panel */}
        <div className="lg:col-span-2">
          <Card variant="glass" className="p-8 shadow-2xl">
            <div className="text-center">
              {!verificationResult ? (
                <>
                  <div className={`w-28 h-28 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg border transition-all duration-300 ${
                    isVerifying 
                      ? 'bg-gradient-to-br from-blue-100/80 to-indigo-100/80 border-blue-200/40 animate-pulse' 
                      : 'bg-gradient-to-br from-emerald-100/80 to-green-100/80 border-green-200/40'
                  }`}>
                    <Shield className={`h-14 w-14 ${
                      isVerifying ? 'text-blue-600' : 'text-green-600'
                    }`} />
                  </div>
                  
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-4">
                    {isVerifying ? 'Verificando...' : 'Listo para Verificar'}
                  </h2>
                  
                  {!isVerifying && (
                    <>
                      <p className="text-gray-700 font-medium mb-8">
                        Presiona el botón y di la siguiente frase:
                      </p>

                      <div className="bg-gradient-to-r from-blue-50/80 to-indigo-50/80 backdrop-blur-sm border border-blue-200/40 rounded-2xl mb-8 p-6 shadow-lg">
                        <p className="text-xl font-semibold text-blue-900">
                          "{phrase}"
                        </p>
                      </div>

                      <Button 
                        size="lg" 
                        className="px-8 shadow-lg hover:shadow-xl"
                        onClick={handleStartVerification}
                      >
                        <Mic className="h-5 w-5 mr-2" />
                        Iniciar Verificación
                      </Button>
                    </>
                  )}

                  {isVerifying && (
                    <div className="space-y-6">
                      <div className="flex justify-center">
                        <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-200/30 border-t-blue-600"></div>
                      </div>
                      <p className="text-blue-700 font-medium text-lg">
                        Analizando tu voz...
                      </p>
                      <div className="bg-blue-100/60 rounded-full h-3 max-w-xs mx-auto shadow-inner">
                        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full animate-pulse shadow-sm" style={{width: '60%'}}></div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                // Resultado de verificación
                <>
                  <div className={`w-28 h-28 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg border transition-all duration-300 ${
                    verificationResult.success 
                      ? 'bg-gradient-to-br from-emerald-100/80 to-green-100/80 border-green-200/40' 
                      : 'bg-gradient-to-br from-red-100/80 to-rose-100/80 border-red-200/40'
                  }`}>
                    {verificationResult.success ? (
                      <CheckCircle className="h-14 w-14 text-green-600" />
                    ) : (
                      <XCircle className="h-14 w-14 text-red-600" />
                    )}
                  </div>
                  
                  <h2 className={`text-3xl font-bold mb-4 ${
                    verificationResult.success 
                      ? 'bg-gradient-to-r from-green-800 to-emerald-700 bg-clip-text text-transparent' 
                      : 'bg-gradient-to-r from-red-800 to-rose-700 bg-clip-text text-transparent'
                  }`}>
                    {verificationResult.success 
                      ? '¡Verificación Exitosa!' 
                      : 'Verificación Fallida'}
                  </h2>
                  
                  <p className={`mb-6 font-medium ${
                    verificationResult.success 
                      ? 'text-green-700' 
                      : 'text-red-700'
                  }`}>
                    {verificationResult.success 
                      ? 'Tu identidad ha sido verificada correctamente.'
                      : 'No se pudo verificar tu identidad. Inténtalo nuevamente.'}
                  </p>

                  <div className="mb-6">
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
                      Nivel de confianza:
                    </p>
                    <div className="bg-gray-100/60 rounded-full h-4 max-w-xs mx-auto shadow-inner">
                      <div 
                        className={`h-4 rounded-full shadow-sm transition-all duration-500 ${
                          verificationResult.success ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-red-500 to-rose-600'
                        }`}
                        style={{width: `${verificationResult.confidence * 100}%`}}
                      ></div>
                    </div>
                    <p className="text-sm font-semibold text-gray-600 dark:text-gray-400 mt-2">
                      {(verificationResult.confidence * 100).toFixed(1)}%
                    </p>
                  </div>

                  <div className="flex space-x-4 justify-center">
                    <Button 
                      variant="secondary"
                      onClick={resetVerification}
                      className="shadow-sm"
                    >
                      Intentar Nuevamente
                    </Button>
                    <Link to="/dashboard">
                      <Button variant="primary" className="shadow-lg">
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
          <Card variant="glass" className="p-6 shadow-xl">
            <h3 className="text-xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-4">
              Proceso de Verificación
            </h3>
            <div className="space-y-4 text-sm">
              <div className="flex items-start">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 backdrop-blur-sm rounded-xl flex items-center justify-center mr-3 shadow-sm border border-blue-200/30">
                  <span className="text-blue-600 text-sm font-bold">1</span>
                </div>
                <p className="text-gray-700 font-medium mt-1">Graba la frase proporcionada</p>
              </div>
              <div className="flex items-start">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 backdrop-blur-sm rounded-xl flex items-center justify-center mr-3 shadow-sm border border-blue-200/30">
                  <span className="text-blue-600 text-sm font-bold">2</span>
                </div>
                <p className="text-gray-700 font-medium mt-1">El sistema analiza tu patrón vocal</p>
              </div>
              <div className="flex items-start">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 backdrop-blur-sm rounded-xl flex items-center justify-center mr-3 shadow-sm border border-blue-200/30">
                  <span className="text-blue-600 text-sm font-bold">3</span>
                </div>
                <p className="text-gray-700 font-medium mt-1">Se compara con tu perfil registrado</p>
              </div>
              <div className="flex items-start">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 backdrop-blur-sm rounded-xl flex items-center justify-center mr-3 shadow-sm border border-blue-200/30">
                  <span className="text-blue-600 text-sm font-bold">4</span>
                </div>
                <p className="text-gray-700 font-medium mt-1">Recibes el resultado de la verificación</p>
              </div>
            </div>
          </Card>

          <div className="bg-gradient-to-r from-blue-50/80 to-cyan-50/80 backdrop-blur-xl border border-blue-200/40 rounded-2xl p-6 shadow-xl">
            <h3 className="text-lg font-bold text-blue-900 mb-4 flex items-center">
              <span className="mr-2">💡</span>
              Consejos
            </h3>
            <ul className="text-sm text-blue-700 space-y-3 font-medium">
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                Habla claramente y a velocidad normal
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                Usa un ambiente silencioso
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                Mantén la misma distancia del micrófono
              </li>
              <li className="flex items-center">
                <span className="w-2 h-2 bg-blue-400 rounded-full mr-3"></span>
                Si falla, espera un momento e inténtalo de nuevo
              </li>
            </ul>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default VerificationPage;