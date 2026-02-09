import { Mic, Clock, Volume2, ShieldCheck, Lock, CheckCircle2, Activity } from 'lucide-react';
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
      title: 'Silencio',
      description: 'Sin ruido de fondo',
      color: 'text-blue-500',
      bg: 'bg-blue-50 dark:bg-blue-900/20',
    },
    {
      icon: Mic,
      title: 'Micrófono',
      description: 'A 15-20cm de distancia',
      color: 'text-purple-500',
      bg: 'bg-purple-50 dark:bg-purple-900/20',
    },
    {
      icon: CheckCircle2,
      title: 'Natural',
      description: 'Habla claro y natural',
      color: 'text-green-500',
      bg: 'bg-green-50 dark:bg-green-900/20',
    },
    {
      icon: Clock,
      title: 'Rápido',
      description: '2-3 minutos aprox.',
      color: 'text-orange-500',
      bg: 'bg-orange-50 dark:bg-orange-900/20',
    },
  ];

  const systemChecks = [
    { label: 'Micrófono detectado', status: 'ready' },
    { label: 'Ambiente verificado', status: 'ready' },
    { label: 'Navegador compatible', status: 'ready' },
  ];

  return (
    <div className={`w-full ${className}`}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-stretch">
        {/* LEFT COLUMN: Hero & Action */}
        <div className="flex flex-col justify-center h-full">
          <Card className="relative overflow-hidden p-10 border-0 shadow-2xl h-full flex flex-col justify-between bg-linear-to-br from-white to-gray-50 dark:from-gray-900 dark:to-gray-800">
            {/* Decorative Background */}
            <div className="absolute top-0 right-0 -mt-20 -mr-20 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

            <div className="relative z-10">
              <div className="mb-8">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-xs font-bold uppercase tracking-wider mb-6">
                  <ShieldCheck className="w-3 h-3" />
                  Registro Seguro
                </div>
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
                  Crea tu <br />
                  <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">
                    Perfil de Voz
                  </span>
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-300 max-w-md leading-relaxed">
                  Registra tu voz para habilitar la autenticación biométrica segura. Grabaremos 3
                  frases simples para crear tu huella vocal única.
                </p>
              </div>

              <div className="space-y-6">
                <Button
                  size="lg"
                  onClick={onStart}
                  className="w-full sm:w-auto px-8 py-4 text-lg shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:-translate-y-0.5 transition-all duration-300 bg-linear-to-r from-blue-600 to-indigo-600 border-0 rounded-xl"
                >
                  <Mic className="h-5 w-5 mr-2" />
                  Comenzar Registro
                </Button>

                <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400">
                  <Lock className="h-4 w-4" />
                  <span>Datos biométricos encriptados</span>
                </div>
              </div>
            </div>

            {/* System Status Mini-Widget */}
            <div className="mt-12 pt-8 border-t border-gray-100 dark:border-gray-800/50">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-4 w-4 text-green-500" />
                <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Sistema Listo
                </span>
              </div>
              <div className="flex flex-wrap gap-3">
                {systemChecks.map((check, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-1.5 bg-gray-50 dark:bg-gray-800/50 px-3 py-1.5 rounded-lg border border-gray-100 dark:border-gray-700/50"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                      {check.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN: Process & Info */}
        <div className="flex flex-col gap-6 h-full">
          {/* Process Steps */}
          <Card className="p-8 border border-gray-100 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 backdrop-blur-sm">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-8 flex items-center gap-2">
              <span className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 text-xs">
                ?
              </span>
              ¿Cómo funciona?
            </h3>

            <div className="space-y-8 relative">
              {/* Connecting Line */}
              <div className="absolute left-6 top-4 bottom-4 w-0.5 bg-gray-100 dark:bg-gray-800" />

              <div className="relative flex items-start gap-6 group">
                <div className="relative z-10 flex items-center justify-center w-12 h-12 rounded-2xl bg-white dark:bg-gray-800 border-2 border-blue-100 dark:border-blue-900/30 text-blue-600 dark:text-blue-400 font-bold text-lg shadow-sm group-hover:scale-110 group-hover:border-blue-500 transition-all duration-300">
                  1
                </div>
                <div className="pt-1">
                  <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-1">
                    Preparación
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Busca un lugar silencioso y asegúrate de que tu micrófono funcione
                    correctamente.
                  </p>
                </div>
              </div>

              <div className="relative flex items-start gap-6 group">
                <div className="relative z-10 flex items-center justify-center w-12 h-12 rounded-2xl bg-white dark:bg-gray-800 border-2 border-indigo-100 dark:border-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-bold text-lg shadow-sm group-hover:scale-110 group-hover:border-indigo-500 transition-all duration-300">
                  2
                </div>
                <div className="pt-1">
                  <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-1">
                    Grabación
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Leerás 3 frases cortas. Nuestro sistema analizará tu voz en tiempo real.
                  </p>
                </div>
              </div>

              <div className="relative flex items-start gap-6 group">
                <div className="relative z-10 flex items-center justify-center w-12 h-12 rounded-2xl bg-white dark:bg-gray-800 border-2 border-green-100 dark:border-green-900/30 text-green-600 dark:text-green-400 font-bold text-lg shadow-sm group-hover:scale-110 group-hover:border-green-500 transition-all duration-300">
                  <CheckCircle2 className="h-6 w-6" />
                </div>
                <div className="pt-1">
                  <h4 className="font-bold text-gray-900 dark:text-white text-lg mb-1">
                    Confirmación
                  </h4>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Tu perfil de voz se creará y podrás usarlo para iniciar sesión de forma segura.
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Recommendations Grid */}
          <div className="grid grid-cols-2 gap-4 flex-1">
            {recommendations.map((rec, index) => {
              const Icon = rec.icon;
              return (
                <Card
                  key={index}
                  className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors border border-gray-100 dark:border-gray-700/50 flex flex-col justify-center items-center text-center gap-3"
                >
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center ${rec.bg}`}
                  >
                    <Icon className={`h-5 w-5 ${rec.color}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm mb-0.5">
                      {rec.title}
                    </h3>
                    <p className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                      {rec.description}
                    </p>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnrollmentWelcomeScreen;
