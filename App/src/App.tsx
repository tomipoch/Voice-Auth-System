import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense } from 'react';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { SettingsModalProvider } from './context/SettingsModalContext';
import { SettingsProvider } from './context/SettingsContext';
import { useAuth } from './hooks/useAuth';
import GlobalSettingsModal from './components/ui/GlobalSettingsModal';
import SkipLink from './components/ui/SkipLink';
import PWAInstallPrompt from './components/ui/PWAInstallPrompt';
import ConnectionStatus from './components/ui/ConnectionStatus';
import ErrorBoundary from './components/ui/ErrorBoundary';

// Lazy load de páginas para code splitting
const LoginPage = lazy(() => import('./pages/LoginPage'));
const RegisterPage = lazy(() => import('./pages/RegisterPage'));
const DashboardPage = lazy(() => import('./pages/DashboardPage'));
const EnrollmentPage = lazy(() => import('./pages/EnrollmentPage'));
const VerificationPage = lazy(() => import('./pages/VerificationPage'));
const HistoryPage = lazy(() => import('./pages/HistoryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
// Admin pages
const AdminDashboardPage = lazy(() => import('./pages/admin/AdminDashboardPage'));
const UsersListPage = lazy(() => import('./pages/admin/UsersListPage'));
const UserDetailPage = lazy(() => import('./pages/admin/UserDetailPage'));
const PhrasesPage = lazy(() => import('./pages/admin/PhrasesPage'));
const AuditLogsPage = lazy(() => import('./pages/admin/AuditLogsPage'));
const SuperAdminDashboard = lazy(() => import('./pages/SuperAdminDashboard'));

// Componente de carga
const LoadingSpinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
    <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 dark:border-blue-400"></div>
  </div>
);

// Componente de rutas protegidas
interface ProtectedRouteProps {
  children: React.ReactNode;
  adminOnly?: boolean;
  superAdminOnly?: boolean;
  userOnly?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  adminOnly = false,
  superAdminOnly = false,
  userOnly = false,
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (superAdminOnly && user?.role !== 'superadmin') {
    return <Navigate to="/dashboard" replace />;
  }

  if (adminOnly && !['admin', 'superadmin'].includes(user?.role ?? '')) {
    return <Navigate to="/dashboard" replace />;
  }

  // Restrict access to regular users only (redirect admins to admin dashboard)
  if (userOnly && ['admin', 'superadmin'].includes(user?.role ?? '')) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  return <>{children}</>;
};

// Componente de rutas públicas (solo para usuarios no autenticados)
interface PublicRouteProps {
  children: React.ReactNode;
}

const PublicRoute: React.FC<PublicRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Componente principal de rutas
const AppRoutes = () => {
  return (
    <>
      <SkipLink />
      <ConnectionStatus />
      <div
        id="main-content"
        className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300"
      >
        <Suspense fallback={<LoadingSpinner />}>
          <Routes>
            {/* Rutas públicas */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicRoute>
                  <RegisterPage />
                </PublicRoute>
              }
            />

            {/* Rutas protegidas para usuarios normales */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute userOnly>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/enrollment"
              element={
                <ProtectedRoute userOnly>
                  <EnrollmentPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/verification"
              element={
                <ProtectedRoute userOnly>
                  <VerificationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <HistoryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />

            {/* Rutas de administrador de empresa */}
            {/* Redirect /admin to /admin/dashboard */}
            <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />

            <Route
              path="/admin/dashboard"
              element={
                <ProtectedRoute adminOnly>
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute adminOnly>
                  <UsersListPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users/:id"
              element={
                <ProtectedRoute adminOnly>
                  <UserDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/phrases"
              element={
                <ProtectedRoute adminOnly>
                  <PhrasesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/logs"
              element={
                <ProtectedRoute adminOnly>
                  <AuditLogsPage />
                </ProtectedRoute>
              }
            />

            {/* Rutas de super administrador */}
            <Route
              path="/super-admin"
              element={
                <ProtectedRoute superAdminOnly>
                  <SuperAdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* Redirección por defecto */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Ruta 404 */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Suspense>

        {/* Modal Global de Configuración */}
        <GlobalSettingsModal />
      </div>

      {/* PWA Install Prompt */}
      <PWAInstallPrompt />
    </>
  );
};

// Cliente de React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutos
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <SettingsProvider>
              <SettingsModalProvider>
                <Router>
                  <AppRoutes />

                  {/* Toast notifications */}
                  <Toaster
                    position="top-right"
                    toastOptions={{
                      duration: 4000,
                      style: {
                        background: '#363636',
                        color: '#fff',
                      },
                      success: {
                        duration: 3000,
                        iconTheme: {
                          primary: '#4ade80',
                          secondary: '#fff',
                        },
                      },
                      error: {
                        duration: 5000,
                        iconTheme: {
                          primary: '#ef4444',
                          secondary: '#fff',
                        },
                      },
                    }}
                  />
                </Router>
              </SettingsModalProvider>
            </SettingsProvider>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
