import { render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { ThemeProvider } from '../../context/ThemeContext';
import { useAuth } from '../../hooks/useAuth';

describe('Authentication Context', () => {
  const wrapper = ({ children }) => (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );

  beforeEach(() => {
    localStorage.clear();
  });

  it('provides authentication context', () => {
    const TestComponent = () => {
      const { user, isAuthenticated } = useAuth();
      return (
        <div>
          <p>Authenticated: {isAuthenticated ? 'yes' : 'no'}</p>
          <p>User: {user?.name || 'none'}</p>
        </div>
      );
    };

    render(<TestComponent />, { wrapper });
    expect(screen.getByText(/Authenticated:/)).toBeInTheDocument();
  });
});
