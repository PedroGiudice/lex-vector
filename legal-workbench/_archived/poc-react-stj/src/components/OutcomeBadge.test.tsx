import { render, screen } from '@testing-library/react';
import { OutcomeBadge } from './OutcomeBadge';

describe('OutcomeBadge', () => {
  it('renders "PROVIDO" badge with success styling', () => {
    render(<OutcomeBadge outcome="provido" />);

    const badge = screen.getByText('PROVIDO');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge-success');
  });

  it('renders "DESPROVIDO" badge with danger styling', () => {
    render(<OutcomeBadge outcome="desprovido" />);

    const badge = screen.getByText('DESPROVIDO');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge-danger');
  });

  it('renders "PARCIAL" badge with warning styling', () => {
    render(<OutcomeBadge outcome="parcial" />);

    const badge = screen.getByText('PARCIAL');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('badge-warning');
  });
});
