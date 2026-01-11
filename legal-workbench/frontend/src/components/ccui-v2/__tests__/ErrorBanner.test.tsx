import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';
import { ErrorBanner } from '../ErrorBanner';

describe('ErrorBanner', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Rendering Different Error Types', () => {
    it('should render connection error with correct styling', () => {
      render(<ErrorBanner type="connection" message="Connection lost" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Connection lost')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-red-500/10');
      expect(screen.getByRole('alert')).toHaveClass('border-red-500/30');
    });

    it('should render timeout error with correct styling', () => {
      render(<ErrorBanner type="timeout" message="Request timed out" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Request timed out')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-yellow-500/10');
      expect(screen.getByRole('alert')).toHaveClass('border-yellow-500/30');
    });

    it('should render server error with correct styling', () => {
      render(<ErrorBanner type="server" message="Server error" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Server error')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-red-500/10');
    });

    it('should render unknown error with correct styling', () => {
      render(<ErrorBanner type="unknown" message="Something went wrong" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-yellow-500/10');
    });

    it('should use default message when message prop is empty', () => {
      render(<ErrorBanner type="connection" message="" />);

      expect(
        screen.getByText('Connection lost. Check your network and try again.')
      ).toBeInTheDocument();
    });

    it('should use default message for each error type', () => {
      const { rerender } = render(<ErrorBanner type="timeout" message="" />);
      expect(
        screen.getByText('Request timed out. The server may be busy.')
      ).toBeInTheDocument();

      rerender(<ErrorBanner type="server" message="" />);
      expect(screen.getByText('Server error. Please try again later.')).toBeInTheDocument();

      rerender(<ErrorBanner type="unknown" message="" />);
      expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
    });
  });

  describe('Auto-dismiss Behavior', () => {
    it('should auto-dismiss non-critical errors after delay', () => {
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="timeout"
          message="Request timed out"
          autoDismiss
          autoDismissDelay={5000}
          onDismiss={onDismiss}
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();

      // Advance timer past autoDismissDelay
      act(() => {
        vi.advanceTimersByTime(5000);
      });

      // Animation starts, wait for animation delay (300ms)
      act(() => {
        vi.advanceTimersByTime(300);
      });

      // onDismiss should be called now
      expect(onDismiss).toHaveBeenCalled();
    });

    it('should NOT auto-dismiss critical errors (connection)', () => {
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="connection"
          message="Connection lost"
          autoDismiss
          autoDismissDelay={5000}
          onDismiss={onDismiss}
        />
      );

      // Advance timer well past autoDismissDelay
      act(() => {
        vi.advanceTimersByTime(10000);
      });

      // Should still be visible
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(onDismiss).not.toHaveBeenCalled();
    });

    it('should NOT auto-dismiss critical errors (server)', () => {
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="server"
          message="Server error"
          autoDismiss
          autoDismissDelay={5000}
          onDismiss={onDismiss}
        />
      );

      act(() => {
        vi.advanceTimersByTime(10000);
      });

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(onDismiss).not.toHaveBeenCalled();
    });

    it('should use custom autoDismissDelay', () => {
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="unknown"
          message="Error"
          autoDismiss
          autoDismissDelay={2000}
          onDismiss={onDismiss}
        />
      );

      // Should not dismiss before delay
      act(() => {
        vi.advanceTimersByTime(1500);
      });
      expect(onDismiss).not.toHaveBeenCalled();

      // Should dismiss after delay
      act(() => {
        vi.advanceTimersByTime(500);
      });

      act(() => {
        vi.advanceTimersByTime(300); // animation delay
      });

      expect(onDismiss).toHaveBeenCalled();
    });

    it('should not auto-dismiss when autoDismiss is false', () => {
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="unknown"
          message="Error"
          autoDismiss={false}
          onDismiss={onDismiss}
        />
      );

      act(() => {
        vi.advanceTimersByTime(10000);
      });

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(onDismiss).not.toHaveBeenCalled();
    });
  });

  describe('Retry Button', () => {
    it('should render retry button when onRetry is provided', () => {
      const onRetry = vi.fn();

      render(<ErrorBanner type="connection" message="Error" onRetry={onRetry} />);

      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should NOT render retry button when onRetry is not provided', () => {
      render(<ErrorBanner type="connection" message="Error" />);

      expect(screen.queryByText('Retry')).not.toBeInTheDocument();
    });

    it('should call onRetry when retry button is clicked', () => {
      const onRetry = vi.fn();

      render(<ErrorBanner type="connection" message="Error" onRetry={onRetry} />);

      fireEvent.click(screen.getByText('Retry'));

      expect(onRetry).toHaveBeenCalledTimes(1);
    });
  });

  describe('Dismiss Button', () => {
    it('should render dismiss button when onDismiss is provided', () => {
      const onDismiss = vi.fn();

      render(<ErrorBanner type="connection" message="Error" onDismiss={onDismiss} />);

      expect(screen.getByLabelText('Dismiss error')).toBeInTheDocument();
    });

    it('should NOT render dismiss button when onDismiss is not provided', () => {
      render(<ErrorBanner type="connection" message="Error" />);

      expect(screen.queryByLabelText('Dismiss error')).not.toBeInTheDocument();
    });

    it('should call onDismiss when dismiss button is clicked after animation', () => {
      const onDismiss = vi.fn();

      render(<ErrorBanner type="connection" message="Error" onDismiss={onDismiss} />);

      fireEvent.click(screen.getByLabelText('Dismiss error'));

      // onDismiss should not be called immediately
      expect(onDismiss).not.toHaveBeenCalled();

      // Wait for exit animation (300ms)
      act(() => {
        vi.advanceTimersByTime(300);
      });

      // Now it should be called
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('should hide banner after dismiss animation', () => {
      const onDismiss = vi.fn();

      render(<ErrorBanner type="connection" message="Error" onDismiss={onDismiss} />);

      fireEvent.click(screen.getByLabelText('Dismiss error'));

      // Should have exit animation class
      expect(screen.getByRole('alert')).toHaveClass('opacity-0');

      // Wait for animation
      act(() => {
        vi.advanceTimersByTime(300);
      });

      // Banner should be hidden now
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Both Buttons', () => {
    it('should render both retry and dismiss buttons', () => {
      const onRetry = vi.fn();
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="connection"
          message="Error"
          onRetry={onRetry}
          onDismiss={onDismiss}
        />
      );

      expect(screen.getByText('Retry')).toBeInTheDocument();
      expect(screen.getByLabelText('Dismiss error')).toBeInTheDocument();
    });

    it('should handle retry click without dismissing', () => {
      const onRetry = vi.fn();
      const onDismiss = vi.fn();

      render(
        <ErrorBanner
          type="connection"
          message="Error"
          onRetry={onRetry}
          onDismiss={onDismiss}
        />
      );

      fireEvent.click(screen.getByText('Retry'));

      expect(onRetry).toHaveBeenCalledTimes(1);
      expect(onDismiss).not.toHaveBeenCalled();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have role="alert"', () => {
      render(<ErrorBanner type="connection" message="Error" />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('should have accessible dismiss button label', () => {
      render(<ErrorBanner type="connection" message="Error" onDismiss={() => {}} />);

      expect(screen.getByLabelText('Dismiss error')).toBeInTheDocument();
    });
  });

  describe('Animation States', () => {
    it('should start with visible animation classes', () => {
      render(<ErrorBanner type="connection" message="Error" />);

      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('opacity-100');
      expect(alert).toHaveClass('translate-y-0');
    });

    it('should add exit animation classes on dismiss', () => {
      render(<ErrorBanner type="connection" message="Error" onDismiss={() => {}} />);

      fireEvent.click(screen.getByLabelText('Dismiss error'));

      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('opacity-0');
      expect(alert).toHaveClass('translate-y-[-10px]');
    });
  });
});
