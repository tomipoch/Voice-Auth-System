import { useState, useEffect } from 'react';
import { useAuth } from './useAuth';
import { adminService } from '../services/apiServices';

export const useDashboardStats = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    verificationsToday: 0,
    successRate: 0,
    totalVerifications: 0,
    isVoiceEnrolled: false,
    loading: true,
    error: null
  });

  const [recentActivity, setRecentActivity] = useState([]);
  const [systemStats, setSystemStats] = useState(null);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setStats(prev => ({ ...prev, loading: true, error: null }));

        // Determinar si el usuario tiene perfil de voz configurado
        const isVoiceEnrolled = user?.voice_template !== null && user?.voice_template !== undefined;

        // Obtener estadísticas del sistema (solo admin)
        let systemData = null;
        if (user?.role === 'admin') {
          try {
            systemData = await adminService.getStats();
            setSystemStats(systemData);
          } catch (error) {
            console.warn('No se pudieron cargar estadísticas del sistema:', error);
          }
        }

        // Estadísticas del usuario basadas en datos mock
        const userStats = {
          verificationsToday: systemData?.total_verifications_today || 
            (isVoiceEnrolled ? Math.floor(Math.random() * 10) + 2 : 0),
          successRate: systemData?.success_rate || 
            (isVoiceEnrolled ? Math.floor(Math.random() * 20) + 80 : 0),
          totalVerifications: isVoiceEnrolled ? Math.floor(Math.random() * 100) + 20 : 0,
          isVoiceEnrolled,
          loading: false,
          error: null
        };

        setStats(userStats);

        // Cargar actividad reciente si es admin
        if (user?.role === 'admin') {
          try {
            const activityData = await adminService.getRecentActivity(5);
            setRecentActivity(activityData);
          } catch (error) {
            console.warn('No se pudo cargar actividad reciente:', error);
            setRecentActivity([]);
          }
        } else {
          // Para usuarios normales, mostrar actividad personal simulada
          setRecentActivity([
            {
              id: 'act-user-1',
              message: 'Verificación de identidad exitosa',
              timestamp: 'hace 5 minutos',
              type: 'success'
            },
            {
              id: 'act-user-2', 
              message: 'Sesión iniciada desde dispositivo móvil',
              timestamp: 'hace 2 horas',
              type: 'info'
            },
            {
              id: 'act-user-3',
              message: isVoiceEnrolled ? 'Perfil de voz actualizado' : 'Pendiente: configurar perfil de voz',
              timestamp: 'hace 1 día',
              type: isVoiceEnrolled ? 'success' : 'warning'
            }
          ]);
        }

      } catch (error) {
        console.error('Error loading dashboard data:', error);
        setStats(prev => ({
          ...prev,
          loading: false,
          error: 'Error al cargar datos del dashboard'
        }));
      }
    };

    if (user) {
      loadDashboardData();
    }
  }, [user]);

  const refreshStats = async () => {
    if (user) {
      // Implementar lógica de refresh si es necesario
      setStats(prev => ({ ...prev, loading: true }));
      // Simular delay
      setTimeout(() => {
        setStats(prev => ({ 
          ...prev, 
          loading: false,
          verificationsToday: prev.verificationsToday + 1 
        }));
      }, 1000);
    }
  };

  return {
    stats,
    recentActivity,
    systemStats,
    refreshStats,
    isLoading: stats.loading
  };
};