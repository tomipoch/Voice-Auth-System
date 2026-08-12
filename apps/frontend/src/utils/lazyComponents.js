import { lazy } from 'react';

/**
 * Lazy load wrapper con retry logic
 * Reintenta cargar el componente si falla (útil para problemas de red)
 */
const lazyWithRetry = (componentImport) => {
  return lazy(() =>
    componentImport().catch((error) => {
      console.error('Error loading component:', error);
      // Reintentar después de 1 segundo
      return new Promise((resolve) => {
        setTimeout(() => {
          resolve(componentImport());
        }, 1000);
      });
    })
  );
};

// Componentes lazy con retry
export const LazyEnrollmentWizard = lazyWithRetry(
  () => import('../components/enrollment/EnrollmentWizard')
);

export const LazyVoiceVerification = lazyWithRetry(
  () => import('../components/verification/VoiceVerification')
);

export const LazyUserManagement = lazyWithRetry(() => import('../components/admin/UserManagement'));

export const LazySystemMetrics = lazyWithRetry(() => import('../components/admin/SystemMetrics'));

export const LazyAudioRecorder = lazyWithRetry(() => import('../components/ui/AudioRecorder'));

// Preload functions para cargar componentes antes de que se necesiten
export const preloadEnrollmentWizard = () => {
  import('../components/enrollment/EnrollmentWizard');
};

export const preloadVoiceVerification = () => {
  import('../components/verification/VoiceVerification');
};

export const preloadAdminComponents = () => {
  import('../components/admin/UserManagement');
  import('../components/admin/SystemMetrics');
};
