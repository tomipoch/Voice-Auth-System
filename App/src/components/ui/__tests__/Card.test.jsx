import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Card from '../Card';

describe('Card Component', () => {
  it('renders children correctly', () => {
    render(
      <Card>
        <h1>Test Card</h1>
      </Card>
    );
    expect(screen.getByText('Test Card')).toBeInTheDocument();
  });

  it('applies default variant', () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('bg-white');
  });

  it('applies glass variant', () => {
    const { container } = render(<Card variant="glass">Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('backdrop-blur-xl');
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass('custom-class');
  });
});
