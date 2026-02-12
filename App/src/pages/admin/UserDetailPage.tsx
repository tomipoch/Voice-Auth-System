import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Calendar, Shield, Mic, Activity, ArrowLeft, CheckCircle, XCircle } from 'lucide-react';
import MainLayout from '../../components/ui/MainLayout';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';

// Mock data - replace with actual API call
const mockUser = {
  id: '1',
  fullName: 'Juan Pérez',
  email: 'juan.perez@example.com',
  role: 'user',
  status: 'active',
  joinedAt: '2024-11-15',
  voiceEnrolled: true,
  lastVerification: '2024-11-30 14:30',
  verificationCount: 12,
  successRate: 92,
};

const mockHistory = [
  { id: 1, date: '2024-11-30 14:30', result: 'success', score: 98, method: 'Frase Aleatoria' },
  { id: 2, date: '2024-11-29 09:15', result: 'success', score: 95, method: 'Frase Fija' },
  { id: 3, date: '2024-11-28 18:45', result: 'failed', score: 45, method: 'Frase Aleatoria' },
];

const UserDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [user] = useState({ ...mockUser, id: id || '1' });
  const [history] = useState(mockHistory);

  return (
    <MainLayout>
      <div className="mb-6">
        <Button
          variant="ghost"
          className="mb-4 pl-0 hover:pl-2 transition-all"
          onClick={() => navigate('/admin')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Volver al Dashboard
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              Detalle de Usuario
            </h1>
            <p className="text-gray-600 dark:text-gray-300">Gestionando a {user.fullName}</p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline">Resetear Password</Button>
            <Button variant="danger">Desactivar Usuario</Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* User Profile Card */}
        <Card className="p-6">
          <div className="flex items-center mb-6">
            <div className="h-16 w-16 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400 text-2xl font-bold mr-4">
              {user.fullName.charAt(0)}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {user.fullName}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-300">{user.email}</p>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 mt-2">
                {user.status}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center text-gray-600 dark:text-gray-300">
                <Shield className="h-4 w-4 mr-2" />
                <span>Rol</span>
              </div>
              <span className="font-medium capitalize">{user.role}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex items-center text-gray-600 dark:text-gray-300">
                <Calendar className="h-4 w-4 mr-2" />
                <span>Registro</span>
              </div>
              <span className="font-medium">{user.joinedAt}</span>
            </div>
          </div>
        </Card>

        {/* Biometric Status Card */}
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <Mic className="h-5 w-5 mr-2 text-purple-600" />
            Estado Biométrico
          </h3>

          <div className="text-center py-4">
            <div
              className={`w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-3 ${
                user.voiceEnrolled
                  ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400'
              }`}
            >
              <Mic className="h-8 w-8" />
            </div>
            <p className="font-bold text-gray-900 dark:text-gray-100 mb-1">
              {user.voiceEnrolled ? 'Voz Registrada' : 'No Registrado'}
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              {user.voiceEnrolled
                ? 'Perfil biométrico activo'
                : 'Usuario pendiente de enrolamiento'}
            </p>

            {user.voiceEnrolled && (
              <Button variant="outline" size="sm" className="w-full">
                Ver Detalles del Modelo
              </Button>
            )}
          </div>
        </Card>

        {/* Stats Card */}
        <Card className="p-6">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-blue-600" />
            Estadísticas
          </h3>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 dark:text-gray-300">Tasa de Éxito</span>
                <span className="font-bold text-gray-900 dark:text-gray-100">
                  {user.successRate}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full"
                  style={{ width: `${user.successRate}%` }}
                ></div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {user.verificationCount}
                </p>
                <p className="text-xs text-blue-600/70 dark:text-blue-400/70">Verificaciones</p>
              </div>
              <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center">
                <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">12</p>
                <p className="text-xs text-purple-600/70 dark:text-purple-400/70">Días Activo</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* History Table */}
      <Card className="p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
          Historial de Verificaciones
        </h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Fecha
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Método
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Resultado
                </th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Score
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
              {history.map((item) => (
                <tr
                  key={item.id}
                  className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <td className="py-3 px-4 text-gray-800 dark:text-gray-200">{item.date}</td>
                  <td className="py-3 px-4 text-gray-700 dark:text-gray-300">{item.method}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        item.result === 'success'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                      }`}
                    >
                      {item.result === 'success' ? (
                        <CheckCircle className="w-3 h-3 mr-1" />
                      ) : (
                        <XCircle className="w-3 h-3 mr-1" />
                      )}
                      {item.result === 'success' ? 'Exitoso' : 'Fallido'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full ${
                            item.score >= 90
                              ? 'bg-green-500'
                              : item.score >= 70
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                          }`}
                          style={{ width: `${item.score}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        {item.score}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </MainLayout>
  );
};

export default UserDetailPage;
