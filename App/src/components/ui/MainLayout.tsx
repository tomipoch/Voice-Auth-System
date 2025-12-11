import Sidebar from './Sidebar';
import type { ReactNode } from 'react';
import { useSessionTimeout } from '../../hooks/useSessionTimeout';

interface MainLayoutProps {
  children: ReactNode;
}

const MainLayout = ({ children }: MainLayoutProps) => {
  // Enable automatic session timeout
  useSessionTimeout();

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <Sidebar />

      {/* Main Content */}
      <main
        id="main-content"
        className="flex-1 overflow-y-auto ml-64"
        role="main"
        aria-label="Contenido principal"
      >
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl">{children}</div>
      </main>
    </div>
  );
};

export default MainLayout;
