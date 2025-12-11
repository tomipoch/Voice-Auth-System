import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import StatusIndicator from '../StatusIndicator';

describe('StatusIndicator', () => {
  it('renders success status', () => {
    const { container } = render(<StatusIndicator status="success" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders error status', () => {
    const { container } = render(<StatusIndicator status="error" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders warning status', () => {
    const { container } = render(<StatusIndicator status="warning" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders pending status', () => {
    const { container } = render(<StatusIndicator status="pending" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders loading status', () => {
    const { container } = render(<StatusIndicator status="loading" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('renders with custom message', () => {
    render(<StatusIndicator status="success" message="Test message" />);
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });

  it('renders without message', () => {
    const { container } = render(<StatusIndicator status="success" />);
    expect(container.firstChild).toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { container } = render(<StatusIndicator status="success" size="lg" />);
    expect(container.firstChild).toBeInTheDocument();
  });
});
