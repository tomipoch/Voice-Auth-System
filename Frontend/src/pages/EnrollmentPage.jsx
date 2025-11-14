import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Mic, Play, Square, RotateCcw } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';

const EnrollmentPage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

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
            Registro de Perfil de Voz
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Para configurar tu autenticación biométrica por voz, necesitamos grabar 
            algunas muestras de tu voz. Este proceso es seguro y tus datos están protegidos.
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Paso {currentStep} de {totalSteps}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round((currentStep / totalSteps) * 100)}% completado
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Content */}
        <Card className="p-8">
          <div className="text-center">
            <div className="w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Mic className="h-12 w-12 text-blue-600" />
            </div>
            
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Grabación {currentStep}
            </h2>
            
            <p className="text-gray-600 mb-8 max-w-md mx-auto">
              Presiona el botón y di la siguiente frase claramente:
            </p>

            <Card className="bg-blue-50 border-blue-200 mb-8 p-6 max-w-lg mx-auto">
              <p className="text-lg font-medium text-blue-900">
                "Mi voz es mi contraseña, úsala para verificar mi identidad"
              </p>
            </Card>

            {/* Recording Controls */}
            <div className="flex flex-col items-center space-y-4">
              <div className="flex space-x-4">
                <Button size="lg" className="px-8">
                  <Mic className="h-5 w-5 mr-2" />
                  Iniciar Grabación
                </Button>
                <Button variant="secondary" size="lg" disabled>
                  <Square className="h-5 w-5 mr-2" />
                  Detener
                </Button>
              </div>
              
              <Button variant="secondary" size="sm" disabled>
                <Play className="h-4 w-4 mr-2" />
                Reproducir
              </Button>
            </div>

            {/* Actions */}
            <div className="flex justify-between items-center mt-8 pt-8 border-t border-gray-200">
              <Button 
                variant="secondary"
                disabled={currentStep === 1}
                onClick={() => setCurrentStep(prev => Math.max(1, prev - 1))}
              >
                Anterior
              </Button>
              
              <Button 
                disabled={currentStep === totalSteps}
                onClick={() => setCurrentStep(prev => Math.min(totalSteps, prev + 1))}
              >
                {currentStep === totalSteps ? 'Finalizar' : 'Siguiente'}
              </Button>
            </div>
          </div>
        </Card>

        {/* Tips */}
        <Card className="mt-6 p-6 bg-yellow-50 border-yellow-200">
          <h3 className="text-lg font-semibold text-yellow-800 mb-3">
            Consejos para una mejor grabación:
          </h3>
          <ul className="text-sm text-yellow-700 space-y-2">
            <li>• Habla de forma natural y clara</li>
            <li>• Asegúrate de estar en un lugar silencioso</li>
            <li>• Mantén el micrófono a una distancia apropiada</li>
            <li>• Si cometes un error, puedes volver a grabar</li>
          </ul>
        </Card>
      </div>
    </div>
  );
};

export default EnrollmentPage;