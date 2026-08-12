import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import SkipLink from '../SkipLink';

describe('SkipLink', () => {
  it('renders skip link', () => {
    render(<SkipLink />);
    const link = screen.getByText(/saltar al contenido principal/i);
    expect(link).toBeInTheDocument();
  });

  it('has correct href attribute', () => {
    render(<SkipLink />);
    const link = screen.getByText(/saltar al contenido principal/i);
    expect(link).toHaveAttribute('href', '#main-content');
  });

  it('renders as anchor element', () => {
    render(<SkipLink />);
    const link = screen.getByText(/saltar al contenido principal/i);
    expect(link.tagName).toBe('A');
  });
});
