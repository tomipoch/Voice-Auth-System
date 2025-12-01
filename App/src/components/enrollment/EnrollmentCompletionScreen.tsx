import { CheckCircle, ArrowRight, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Button from '../ui/Button';
import Card from '../ui/Card';

interface EnrollmentCompletionScreenProps {
  samplesRecorded?: number;
  qualityScore?: number;
  className?: string;
}

const EnrollmentCompletionScreen = ({
  samplesRecorded = 3,
  qualityScore,
  className = '',
}: EnrollmentCompletionScreenProps) => {
  const navigate = useNavigate();

  return (
    <div className={`max-w-2xl mx-auto ${className}`}>
      <Card variant="glass" className="p-8 text-center">
        {/* Success Icon */}
        <div className="w-32 h-32 bg-linear-to-br from-green-100/80 to-emerald-100/80 backdrop-blur-sm rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg border border-green-200/40 animate-bounce-slow">
          <CheckCircle className="h-16 w-16 text-green-600" />
        </div>

        {/* Title */}
        <h2 className="text-3xl font-bold bg-linear-to-r from-green-600 to-emerald-600 dark:from-green-400 dark:to-emerald-400 bg-clip-text text-transparent mb-4">
          ¡Registro Completado!
        </h2>

        <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
          Tu perfil de voz ha sido creado exitosamente. Ahora puedes usar tu voz para autenticarte
          de forma segura.
        </p>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 mb-8">
          <Card className="p-4 bg-linear-to-br from-blue-50/80 to-indigo-50/80 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200/40 dark:border-blue-700/40">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Muestras Grabadas</p>
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">{samplesRecorded}</p>
          </Card>

          {qualityScore !== undefined && (
            <Card className="p-4 bg-linear-to-br from-green-50/80 to-emerald-50/80 dark:from-green-900/20 dark:to-emerald-900/20 border-green-200/40 dark:border-green-700/40">
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Calidad Promedio</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                {(qualityScore * 100).toFixed(0)}%
              </p>
            </Card>
          )}
        </div>

        {/* Next Steps */}
        <Card className="p-6 bg-linear-to-r from-amber-50/80 to-yellow-50/80 dark:from-amber-900/20 dark:to-yellow-900/20 border-amber-200/40 dark:border-amber-700/40 mb-8">
          <h3 className="text-lg font-semibold text-amber-800 dark:text-amber-300 mb-3">
            ¿Qué sigue?
          </h3>
          <ul className="text-sm text-amber-700 dark:text-amber-400 space-y-2 text-left">
            <li className="flex items-start">
              <ArrowRight className="h-4 w-4 mr-2 mt-0.5 shrink-0" />
              <span>Puedes ir a la sección de Verificación para probar tu perfil de voz</span>
            </li>
            <li className="flex items-start">
              <ArrowRight className="h-4 w-4 mr-2 mt-0.5 shrink-0" />
              <span>Tu voz ahora está protegida con encriptación de nivel bancario</span>
            </li>
            <li className="flex items-start">
              <ArrowRight className="h-4 w-4 mr-2 mt-0.5 shrink-0" />
              <span>Puedes actualizar tu perfil en cualquier momento desde Configuración</span>
            </li>
          </ul>
        </Card>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            size="lg"
            onClick={() => navigate('/verification')}
            className="px-8 shadow-lg hover:shadow-xl"
          >
            Probar Verificación
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>

          <Button
            variant="secondary"
            size="lg"
            onClick={() => navigate('/dashboard')}
            className="px-8"
          >
            <Home className="h-5 w-5 mr-2" />
            Ir al Dashboard
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default EnrollmentCompletionScreen;
