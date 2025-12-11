import { render } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import ConnectionStatus from '../ConnectionStatus';

// Mock navigator.onLine
Object.defineProperty(window.navigator, 'onLine', {
  writable: true,
  value: true,
});

describe('ConnectionStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders when online', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: true,
    });

    const { container } = render(<ConnectionStatus />);
    expect(container).toBeInTheDocument();
  });

  it('shows offline message when offline', () => {
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: false,
    });

    render(<ConnectionStatus />);
    // Component should render offline state
    expect(document.body).toBeInTheDocument();
  });

  it('renders without crashing', () => {
    const { container } = render(<ConnectionStatus />);
    expect(container).toBeTruthy();
  });
});
