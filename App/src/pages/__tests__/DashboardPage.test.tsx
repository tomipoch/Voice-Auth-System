import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from '../DashboardPage';
import { AuthContext } from '../../context/AuthContext';
import { verificationService } from '../../services/apiServices';

// Mock the services
vi.mock('../../services/apiServices', () => ({
  verificationService: {
    getVerificationHistory: vi.fn(),
  },
}));

// Helper to render with providers
const renderWithProviders = (ui: React.ReactElement, { user = null } = {}) => {
  const mockAuthContext = {
    user,
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
    refreshUser: vi.fn(),
  };

  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContext}>{ui}</AuthContext.Provider>
    </BrowserRouter>
  );
};

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard with user data', async () => {
    const mockUser = {
      id: '1',
      name: 'John Doe',
      email: 'john@example.com',
      role: 'user',
      voice_template: null,
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText(/¡Bienvenido, John!/i)).toBeInTheDocument();
    });
  });

  it('shows welcome message with user name', async () => {
    const mockUser = {
      id: '1',
      name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'user',
      voice_template: null,
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText(/¡Bienvenido, Jane!/i)).toBeInTheDocument();
    });
  });

  it('displays quick actions section', async () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      voice_template: null,
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText('Acciones Rápidas')).toBeInTheDocument();
    });
  });

  it('shows enrollment status correctly when not enrolled', async () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      voice_template: null, // Not enrolled
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText(/Registrar Perfil de Voz/i)).toBeInTheDocument();
    });
  });

  it('shows enrollment status correctly when enrolled', async () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      voice_template: 'template_data', // Enrolled
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText(/Actualizar Perfil de Voz/i)).toBeInTheDocument();
    });
  });

  it('hides admin panel for non-admin users', async () => {
    const mockUser = {
      id: '1',
      name: 'Regular User',
      email: 'user@example.com',
      role: 'user', // Regular user
      voice_template: null,
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.queryByText(/Panel Administrativo/i)).not.toBeInTheDocument();
    });
  });

  it('shows admin panel for admin users', async () => {
    const mockUser = {
      id: '1',
      name: 'Admin User',
      email: 'admin@example.com',
      role: 'admin', // Admin user
      voice_template: null,
    };

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: [],
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText('Panel de control administrativo')).toBeInTheDocument();
    });
  });

  it('displays recent activity when available', async () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      voice_template: 'template',
    };

    const mockHistory = [
      {
        result: 'success',
        score: 95,
        date: '2024-01-01T10:00:00Z',
      },
      {
        result: 'failure',
        score: 45,
        date: '2024-01-01T09:00:00Z',
      },
    ];

    vi.mocked(verificationService.getVerificationHistory).mockResolvedValue({
      success: true,
      history: mockHistory,
    });

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(screen.getByText(/Verificación exitosa \(95%\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Verificación fallida \(45%\)/i)).toBeInTheDocument();
    });
  });

  it('handles loading state', async () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      voice_template: null,
    };

    // Simulate slow API response
    vi.mocked(verificationService.getVerificationHistory).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                success: true,
                history: [],
              }),
            100
          )
        )
    );

    renderWithProviders(<DashboardPage />, { user: mockUser });

    // Component should render even during loading
    expect(screen.getByText(/¡Bienvenido/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(verificationService.getVerificationHistory).toHaveBeenCalledWith(mockUser.id, 5);
    });
  });

  it('handles error state when fetching history fails', async () => {
    const mockUser = {
      id: '1',
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      voice_template: null,
    };

    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    vi.mocked(verificationService.getVerificationHistory).mockRejectedValue(
      new Error('API Error')
    );

    renderWithProviders(<DashboardPage />, { user: mockUser });

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error fetching history:',
        expect.any(Error)
      );
    });

    // Page should still render despite error
    expect(screen.getByText(/¡Bienvenido/i)).toBeInTheDocument();

    consoleErrorSpy.mockRestore();
  });
});
