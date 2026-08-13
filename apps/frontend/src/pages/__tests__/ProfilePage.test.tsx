/**
 * ProfilePage tests against the typed AuthService.
 *
 * Mirrors what an admin user can do from the profile page: edit
 * personal fields and change the password. Mocks the new
 * services/authService module (replacing the legacy apiServices
 * facade) and verifies the user-visible toasts.
 */

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import ProfilePage from '../ProfilePage';
import { AuthContext } from '../../context/AuthContext';
import toast from 'react-hot-toast';
import type { AuthContextValue } from '../../context/AuthContext';

vi.mock('../../services/authService', () => ({
  authService: {
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    refreshToken: vi.fn(),
    getProfile: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn(), info: vi.fn() },
}));

type AuthUser = NonNullable<AuthContextValue['user']>;

const renderWithProviders = (
  ui: React.ReactElement,
  { user = null as AuthUser | null }: { user?: AuthUser | null } = {},
) => {
  const mockAuthContext = {
    user,
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
    refreshUser: vi.fn(),
  } as unknown as AuthContextValue;

  return render(
    <BrowserRouter>
      <AuthContext.Provider value={mockAuthContext}>{ui}</AuthContext.Provider>
    </BrowserRouter>
  );
};

import { authService } from '../../services/authService';

const mockedUpdateProfile = vi.mocked(authService.updateProfile);
const mockedChangePassword = vi.mocked(authService.changePassword);

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockUser = {
    id: '1',
    name: 'John Doe',
    email: 'john@example.com',
    role: 'user',
    first_name: 'John',
    last_name: 'Doe',
    company: 'Test Company',
    created_at: '2024-01-01T00:00:00Z',
  };

  it('renders profile with user data', () => {
    renderWithProviders(<ProfilePage />, { user: mockUser });

    expect(screen.getByText('Mi Perfil')).toBeInTheDocument();
    expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
  });

  it('shows user initials correctly', () => {
    renderWithProviders(<ProfilePage />, { user: mockUser });
    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('disables email and company fields', () => {
    renderWithProviders(<ProfilePage />, { user: mockUser });

    expect(screen.getByDisplayValue('john@example.com')).toBeDisabled();
    expect(screen.getByDisplayValue('Test Company')).toBeDisabled();
  });

  it('enables editing mode on button click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProfilePage />, { user: mockUser });

    const editButton = screen.getByRole('button', { name: /editar/i });
    await user.click(editButton);

    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
  });

  it('saves profile changes successfully', async () => {
    const user = userEvent.setup();
    const mockRefreshUser = vi.fn();

    mockedUpdateProfile.mockResolvedValue({ success: true, message: 'Profile updated' });

    const mockAuthContext = {
      user: mockUser,
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
      refreshUser: mockRefreshUser,
    } as unknown as AuthContextValue;

    render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <ProfilePage />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    await user.click(screen.getByRole('button', { name: /editar/i }));

    const firstNameInput = screen.getByDisplayValue('John');
    await user.clear(firstNameInput);
    await user.type(firstNameInput, 'Jane');

    await user.click(screen.getByRole('button', { name: /guardar cambios/i }));

    await waitFor(() => {
      expect(mockedUpdateProfile).toHaveBeenCalledWith({
        first_name: 'Jane',
        last_name: 'Doe',
        company: 'Test Company',
      });
      expect(toast.success).toHaveBeenCalledWith('Perfil actualizado exitosamente');
      expect(mockRefreshUser).toHaveBeenCalled();
    });
  });

  it('shows error on save failure', async () => {
    const user = userEvent.setup();

    mockedUpdateProfile.mockResolvedValue({
      success: false,
      message: 'Update failed',
    });

    renderWithProviders(<ProfilePage />, { user: mockUser });

    await user.click(screen.getByRole('button', { name: /editar/i }));
    await user.click(screen.getByRole('button', { name: /guardar cambios/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Update failed');
    });
  });

  it('toggles password change section', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProfilePage />, { user: mockUser });

    expect(screen.queryByText(/contraseña actual/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    expect(screen.getByText(/contraseña actual/i)).toBeInTheDocument();
    expect(screen.getAllByText(/nueva contraseña/i).length).toBeGreaterThan(0);
  });

  it('shows password strength indicator', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    const newPasswordInput = container.querySelector(
      'input[name="newPassword"]',
    ) as HTMLInputElement;
    await user.type(newPasswordInput, 'weak');

    await waitFor(() => {
      expect(screen.getByText(/débil/i)).toBeInTheDocument();
    });

    await user.clear(newPasswordInput);
    await user.type(newPasswordInput, 'Strong@Pass123');

    await waitFor(() => {
      expect(screen.getByText(/fuerte/i)).toBeInTheDocument();
    });
  });

  it('validates password match', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    const newPasswordInput = container.querySelector(
      'input[name="newPassword"]',
    ) as HTMLInputElement;
    const confirmPasswordInput = container.querySelector(
      'input[name="confirmPassword"]',
    ) as HTMLInputElement;

    await user.type(newPasswordInput, 'Password123!');
    await user.type(confirmPasswordInput, 'Different123!');

    await waitFor(() => {
      expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument();
    });
  });

  it('successfully changes password', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    mockedChangePassword.mockResolvedValue({
      success: true,
      message: 'Password changed',
    });

    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await user.type(
      container.querySelector('input[name="currentPassword"]') as HTMLInputElement,
      'OldPassword123!',
    );
    await user.type(
      container.querySelector('input[name="newPassword"]') as HTMLInputElement,
      'NewPassword123!',
    );
    await user.type(
      container.querySelector('input[name="confirmPassword"]') as HTMLInputElement,
      'NewPassword123!',
    );

    await user.click(screen.getByRole('button', { name: /actualizar contraseña/i }));

    await waitFor(() => {
      expect(mockedChangePassword).toHaveBeenCalledWith(
        'OldPassword123!',
        'NewPassword123!',
      );
      expect(toast.success).toHaveBeenCalledWith('Contraseña actualizada exitosamente');
    });
  });

  it('shows error on password change failure', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    mockedChangePassword.mockRejectedValue({
      response: { data: { detail: 'Current password is incorrect' } },
    });

    await user.click(screen.getByRole('button', { name: /cambiar contraseña/i }));

    await user.type(
      container.querySelector('input[name="currentPassword"]') as HTMLInputElement,
      'WrongPassword',
    );
    await user.type(
      container.querySelector('input[name="newPassword"]') as HTMLInputElement,
      'NewPassword123!',
    );
    await user.type(
      container.querySelector('input[name="confirmPassword"]') as HTMLInputElement,
      'NewPassword123!',
    );

    await user.click(screen.getByRole('button', { name: /actualizar contraseña/i }));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Current password is incorrect');
    });
  });
});
