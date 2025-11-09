import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mic, Play, Square, RotateCcw } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const EnrollmentPage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Animated Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cyan-400/20 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Link 
            to="/dashboard" 
            className="flex items-center px-4 py-2 text-blue-600 hover:text-blue-700 transition-all duration-300 bg-white/70 backdrop-blur-xl border border-blue-200/40 rounded-xl hover:bg-white/80 hover:shadow-md"
          >
            <ArrowLeft className="h-5 w-5 mr-2" />
            Volver al Dashboard
          </Link>
        </div>

        {/* Título */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-800 via-blue-700 to-indigo-800 bg-clip-text text-transparent mb-4">
            Registro de Perfil de Voz
          </h1>
          <p className="text-lg text-blue-600/80 font-medium max-w-2xl mx-auto">
            Para configurar tu autenticación biométrica por voz, necesitamos grabar 
            algunas muestras de tu voz. Este proceso es seguro y tus datos están protegidos.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="backdrop-blur-xl bg-white/70 border border-blue-200/40 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-gray-700">
                Paso {currentStep} de {totalSteps}
              </span>
              <span className="text-sm text-blue-600/70 font-medium">
                {Math.round((currentStep / totalSteps) * 100)}% completado
              </span>
            </div>
            <div className="w-full bg-blue-100/60 rounded-full h-3 shadow-inner">
              <div 
                className="bg-gradient-to-r from-blue-500 to-indigo-600 h-3 rounded-full transition-all duration-500 shadow-sm"
                style={{ width: `${(currentStep / totalSteps) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <Card variant="glass" className="p-8 shadow-2xl">
          <div className="text-center">
            <div className="w-28 h-28 bg-gradient-to-br from-blue-100/80 to-indigo-100/80 backdrop-blur-sm rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg border border-blue-200/40">
              <Mic className="h-14 w-14 text-blue-600" />
            </div>
            
            <h2 className="text-3xl font-bold bg-gradient-to-r from-gray-800 to-blue-700 bg-clip-text text-transparent mb-4">
              Grabación {currentStep}
            </h2>
            
            <p className="text-gray-700 mb-8 max-w-md mx-auto font-medium">
              Presiona el botón y di la siguiente frase claramente:
            </p>

            <div className="bg-gradient-to-r from-blue-50/80 to-indigo-50/80 backdrop-blur-sm border border-blue-200/40 rounded-2xl mb-8 p-6 max-w-lg mx-auto shadow-lg">
              <p className="text-xl font-semibold text-blue-900">
                "Mi voz es mi contraseña, úsala para verificar mi identidad"
              </p>
            </div>

            {/* Recording Controls */}
            <div className="flex flex-col items-center space-y-6">
              <div className="flex space-x-4">
                <Button size="lg" className="px-8 shadow-lg hover:shadow-xl">
                  <Mic className="h-5 w-5 mr-2" />
                  Iniciar Grabación
                </Button>
                <Button variant="glass" size="lg" disabled className="px-8">
                  <Square className="h-5 w-5 mr-2" />
                  Detener
                </Button>
              </div>
              
              <Button variant="secondary" size="sm" disabled className="shadow-sm">
                <Play className="h-4 w-4 mr-2" />
                Reproducir
              </Button>
            </div>

            {/* Actions */}
            <div className="flex justify-between items-center mt-8 pt-8 border-t border-blue-200/40">
              <Button 
                variant="secondary"
                disabled={currentStep === 1}
                onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
                className="shadow-sm"
              >
                Anterior
              </Button>
              
              <Button 
                disabled={currentStep === totalSteps}
                onClick={() => setCurrentStep(prev => Math.min(totalSteps, prev + 1))}
                className="shadow-lg"
              >
                {currentStep === totalSteps ? 'Finalizar' : 'Siguiente'}
              </Button>
            </div>
          </div>
        </Card>

        {/* Tips */}
        <div className="mt-8 backdrop-blur-xl bg-gradient-to-r from-amber-50/80 to-yellow-50/80 border border-amber-200/40 rounded-2xl p-6 shadow-xl">
          <h3 className="text-lg font-bold text-amber-800 mb-4 flex items-center">
            <span className="mr-2">💡</span>
            Consejos para una mejor grabación:
          </h3>
          <ul className="text-sm text-amber-700 space-y-3 font-medium">
            <li className="flex items-center">
              <span className="w-2 h-2 bg-amber-400 rounded-full mr-3"></span>
              Habla de forma natural y clara
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-amber-400 rounded-full mr-3"></span>
              Asegúrate de estar en un lugar silencioso
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-amber-400 rounded-full mr-3"></span>
              Mantén el micrófono a una distancia apropiada
            </li>
            <li className="flex items-center">
              <span className="w-2 h-2 bg-amber-400 rounded-full mr-3"></span>
              Si cometes un error, puedes volver a grabar
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default EnrollmentPage;