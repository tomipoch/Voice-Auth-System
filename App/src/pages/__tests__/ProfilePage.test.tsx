// @ts-nocheck
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import ProfilePage from '../ProfilePage';
import { AuthContext } from '../../context/AuthContext';
import { authService } from '../../services/apiServices';
import toast from 'react-hot-toast';

// Mock the services and toast
vi.mock('../../services/apiServices', () => ({
  authService: {
    updateProfile: vi.fn(),
    changePassword: vi.fn(),
  },
}));

vi.mock('react-hot-toast', () => ({
  default: {
    success: vi.fn(),
    error: vi.fn(),
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

    // The initials should be "JD" for John Doe
    expect(screen.getByText('JD')).toBeInTheDocument();
  });

  it('displays editable fields (firstName, lastName)', () => {
    renderWithProviders(<ProfilePage />, { user: mockUser });

    const firstNameInput = screen.getByDisplayValue('John');
    const lastNameInput = screen.getByDisplayValue('Doe');

    expect(firstNameInput).toBeInTheDocument();
    expect(lastNameInput).toBeInTheDocument();
  });

  it('disables email and company fields', () => {
    renderWithProviders(<ProfilePage />, { user: mockUser });

    const emailInput = screen.getByDisplayValue('john@example.com');
    const companyInput = screen.getByDisplayValue('Test Company');

    expect(emailInput).toBeDisabled();
    expect(companyInput).toBeDisabled();
  });

  it('enables editing mode on button click', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProfilePage />, { user: mockUser });

    const editButton = screen.getByRole('button', { name: /editar/i });
    await user.click(editButton);

    // After clicking edit, the button should change to "Cancelar"
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
  });

  it('saves profile changes successfully', async () => {
    const user = userEvent.setup();
    const mockRefreshUser = vi.fn();

    vi.mocked(authService.updateProfile).mockResolvedValue({
      success: true,
    });

    const mockAuthContext = {
      user: mockUser,
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
      refreshUser: mockRefreshUser,
    };

    render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <ProfilePage />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    // Click edit button
    const editButton = screen.getByRole('button', { name: /editar/i });
    await user.click(editButton);

    // Change first name
    const firstNameInput = screen.getByDisplayValue('John');
    await user.clear(firstNameInput);
    await user.type(firstNameInput, 'Jane');

    // Click save
    const saveButton = screen.getByRole('button', { name: /guardar cambios/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(authService.updateProfile).toHaveBeenCalledWith({
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

    vi.mocked(authService.updateProfile).mockResolvedValue({
      success: false,
      error: 'Update failed',
    });

    renderWithProviders(<ProfilePage />, { user: mockUser });

    // Click edit button
    const editButton = screen.getByRole('button', { name: /editar/i });
    await user.click(editButton);

    // Click save
    const saveButton = screen.getByRole('button', { name: /guardar cambios/i });
    await user.click(saveButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Update failed');
    });
  });

  it('toggles password change section', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ProfilePage />, { user: mockUser });

    // Initially, password section should not be visible
    expect(screen.queryByText(/contraseña actual/i)).not.toBeInTheDocument();

    // Click "Cambiar Contraseña" button
    const changePasswordButton = screen.getByRole('button', { name: /cambiar contraseña/i });
    await user.click(changePasswordButton);

    // Now password section should be visible - check for "Contraseña Actual" which is unique
    expect(screen.getByText(/contraseña actual/i)).toBeInTheDocument();
    // Check that there are multiple "nueva contraseña" labels (one for new, one for confirm)
    const newPasswordLabels = screen.getAllByText(/nueva contraseña/i);
    expect(newPasswordLabels.length).toBeGreaterThan(0);
  });

  it('shows password strength indicator', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    // Open password section
    const changePasswordButton = screen.getByRole('button', { name: /cambiar contraseña/i });
    await user.click(changePasswordButton);

    // Find password input by name attribute
    const newPasswordInput = container.querySelector(
      'input[name="newPassword"]'
    ) as HTMLInputElement;
    expect(newPasswordInput).toBeInTheDocument();

    // Type a weak password
    await user.type(newPasswordInput, 'weak');

    // Should show "Débil"
    await waitFor(() => {
      expect(screen.getByText(/débil/i)).toBeInTheDocument();
    });

    // Type a strong password
    await user.clear(newPasswordInput);
    await user.type(newPasswordInput, 'Strong@Pass123');

    // Should show "Fuerte"
    await waitFor(() => {
      expect(screen.getByText(/fuerte/i)).toBeInTheDocument();
    });
  });

  it('validates password match', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    // Open password section
    const changePasswordButton = screen.getByRole('button', { name: /cambiar contraseña/i });
    await user.click(changePasswordButton);

    // Find inputs by name attribute
    const newPasswordInput = container.querySelector(
      'input[name="newPassword"]'
    ) as HTMLInputElement;
    const confirmPasswordInput = container.querySelector(
      'input[name="confirmPassword"]'
    ) as HTMLInputElement;

    // Type passwords that don't match
    await user.type(newPasswordInput, 'Password123!');
    await user.type(confirmPasswordInput, 'Different123!');

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/las contraseñas no coinciden/i)).toBeInTheDocument();
    });
  });

  it('successfully changes password', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    vi.mocked(authService.changePassword).mockResolvedValue({
      success: true,
    });

    // Open password section
    const changePasswordButton = screen.getByRole('button', { name: /cambiar contraseña/i });
    await user.click(changePasswordButton);

    // Find inputs by name attribute
    const currentPasswordInput = container.querySelector(
      'input[name="currentPassword"]'
    ) as HTMLInputElement;
    const newPasswordInput = container.querySelector(
      'input[name="newPassword"]'
    ) as HTMLInputElement;
    const confirmPasswordInput = container.querySelector(
      'input[name="confirmPassword"]'
    ) as HTMLInputElement;

    // Fill in password fields
    await user.type(currentPasswordInput, 'OldPassword123!');
    await user.type(newPasswordInput, 'NewPassword123!');
    await user.type(confirmPasswordInput, 'NewPassword123!');

    // Submit
    const updateButton = screen.getByRole('button', { name: /actualizar contraseña/i });
    await user.click(updateButton);

    await waitFor(() => {
      expect(authService.changePassword).toHaveBeenCalledWith('OldPassword123!', 'NewPassword123!');
      expect(toast.success).toHaveBeenCalledWith('Contraseña actualizada exitosamente');
    });
  });

  it('shows error on password change failure', async () => {
    const user = userEvent.setup();
    const { container } = renderWithProviders(<ProfilePage />, { user: mockUser });

    vi.mocked(authService.changePassword).mockResolvedValue({
      success: false,
      error: 'Current password is incorrect',
    });

    // Open password section
    const changePasswordButton = screen.getByRole('button', { name: /cambiar contraseña/i });
    await user.click(changePasswordButton);

    // Find inputs by name attribute
    const currentPasswordInput = container.querySelector(
      'input[name="currentPassword"]'
    ) as HTMLInputElement;
    const newPasswordInput = container.querySelector(
      'input[name="newPassword"]'
    ) as HTMLInputElement;
    const confirmPasswordInput = container.querySelector(
      'input[name="confirmPassword"]'
    ) as HTMLInputElement;

    // Fill in password fields
    await user.type(currentPasswordInput, 'WrongPassword');
    await user.type(newPasswordInput, 'NewPassword123!');
    await user.type(confirmPasswordInput, 'NewPassword123!');

    // Submit
    const updateButton = screen.getByRole('button', { name: /actualizar contraseña/i });
    await user.click(updateButton);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Current password is incorrect');
    });
  });
});
