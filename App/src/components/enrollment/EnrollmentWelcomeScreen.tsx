import { Mic, Clock, Volume2, CheckCircle, ArrowRight } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

interface EnrollmentWelcomeScreenProps {
  onStart: () => void;
  className?: string;
}

const EnrollmentWelcomeScreen = ({ onStart, className = '' }: EnrollmentWelcomeScreenProps) => {
  const recommendations = [
    {
      icon: Volume2,
      title: 'Ambiente Silencioso',
      description: 'Busca un lugar tranquilo sin ruido de fondo',
    },
    {
      icon: Mic,
      title: 'Micrófono Apropiado',
      description: 'Mantén el micrófono a 15-20cm de distancia',
    },
    {
      icon: CheckCircle,
      title: 'Habla Natural',
      description: 'Lee las frases de forma clara y natural',
    },
    {
      icon: Clock,
      title: 'Tiempo Estimado',
      description: '2-3 minutos para completar el registro',
    },
  ];

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      {/* Hero Section */}
      <Card variant="glass" className="p-8 mb-6 text-center">
        <div className="w-32 h-32 bg-linear-to-br from-blue-100/80 to-indigo-100/80 backdrop-blur-sm rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg border border-blue-200/40">
          <Mic className="h-16 w-16 text-blue-600" />
        </div>

        <h2 className="text-3xl font-bold bg-linear-to-r from-gray-800 to-blue-700 dark:from-gray-200 dark:to-blue-400 bg-clip-text text-transparent mb-4">
          Registro de Perfil de Voz
        </h2>

        <p className="text-lg text-gray-600 dark:text-gray-300 mb-6 max-w-2xl mx-auto">
          Vamos a crear tu perfil biométrico de voz. Grabaremos{' '}
          <span className="font-semibold text-blue-600 dark:text-blue-400">3 frases</span> que te
          ayudarán a autenticarte de forma segura en el futuro.
        </p>

        <div className="flex items-center justify-center space-x-2 text-sm text-blue-600/70 dark:text-blue-400/70">
          <Clock className="h-4 w-4" />
          <span className="font-medium">Tiempo estimado: 2-3 minutos</span>
        </div>
      </Card>

      {/* Recommendations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {recommendations.map((rec, index) => {
          const Icon = rec.icon;
          return (
            <Card
              key={index}
              variant="glass"
              className="p-6 hover:shadow-lg transition-all duration-300 group"
            >
              <div className="flex items-start space-x-4">
                <div className="w-12 h-12 bg-linear-to-br from-blue-100/80 to-indigo-100/80 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-300">
                  <Icon className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800 dark:text-gray-200 mb-1">
                    {rec.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{rec.description}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Process Flow */}
      <Card variant="glass" className="p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 text-center">
          ¿Cómo funciona?
        </h3>
        <div className="flex items-center justify-center space-x-4 text-sm">
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-2">
              <span className="font-bold text-blue-600 dark:text-blue-400">1</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-center">
              Verás la
              <br />
              frase
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-400" />
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-2">
              <span className="font-bold text-blue-600 dark:text-blue-400">2</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-center">
              Countdown
              <br />
              3-2-1
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-400" />
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-2">
              <span className="font-bold text-blue-600 dark:text-blue-400">3</span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-center">
              Lee la
              <br />
              frase
            </p>
          </div>
          <ArrowRight className="h-5 w-5 text-gray-400" />
          <div className="flex flex-col items-center">
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mb-2">
              <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
            </div>
            <p className="text-gray-600 dark:text-gray-400 text-center">
              Repetir
              <br />3 veces
            </p>
          </div>
        </div>
      </Card>

      {/* Start Button */}
      <div className="text-center">
        <Button
          size="lg"
          onClick={onStart}
          className="px-12 py-4 text-lg shadow-xl hover:shadow-2xl transform hover:scale-105 transition-all duration-300"
        >
          <Mic className="h-6 w-6 mr-3" />
          Comenzar Registro
        </Button>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
          Asegúrate de tener el micrófono habilitado
        </p>
      </div>
    </div>
  );
};

export default EnrollmentWelcomeScreen;
