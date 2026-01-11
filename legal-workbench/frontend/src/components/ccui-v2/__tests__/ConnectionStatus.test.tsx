import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { ConnectionStatus, ConnectionState } from '../ConnectionStatus';

describe('ConnectionStatus', () => {
  describe('Status Dot Colors', () => {
    it('should render green dot for connected status', () => {
      render(<ConnectionStatus status="connected" />);

      const dots = document.querySelectorAll('.rounded-full');
      const mainDot = dots[dots.length - 1]; // Get the actual dot, not the pulse
      expect(mainDot).toHaveClass('bg-green-500');
    });

    it('should render yellow dot for connecting status', () => {
      render(<ConnectionStatus status="connecting" />);

      const dots = document.querySelectorAll('.rounded-full');
      const mainDot = dots[dots.length - 1];
      expect(mainDot).toHaveClass('bg-yellow-500');
    });

    it('should render red dot for disconnected status', () => {
      render(<ConnectionStatus status="disconnected" />);

      const dots = document.querySelectorAll('.rounded-full');
      const mainDot = dots[dots.length - 1];
      expect(mainDot).toHaveClass('bg-red-500');
    });

    it('should render red dot for error status', () => {
      render(<ConnectionStatus status="error" />);

      const dots = document.querySelectorAll('.rounded-full');
      const mainDot = dots[dots.length - 1];
      expect(mainDot).toHaveClass('bg-red-500');
    });

    it('should render gray dot for disabled status', () => {
      render(<ConnectionStatus status="disabled" />);

      const dots = document.querySelectorAll('.rounded-full');
      const mainDot = dots[dots.length - 1];
      expect(mainDot).toHaveClass('bg-gray-500');
    });
  });

  describe('Pulse Animation', () => {
    it('should show pulse animation for connecting status', () => {
      render(<ConnectionStatus status="connecting" />);

      const pulseElement = document.querySelector('.animate-ping');
      expect(pulseElement).toBeInTheDocument();
    });

    it('should NOT show pulse animation for connected status', () => {
      render(<ConnectionStatus status="connected" />);

      const pulseElement = document.querySelector('.animate-ping');
      expect(pulseElement).not.toBeInTheDocument();
    });

    it('should NOT show pulse animation for disconnected status', () => {
      render(<ConnectionStatus status="disconnected" />);

      const pulseElement = document.querySelector('.animate-ping');
      expect(pulseElement).not.toBeInTheDocument();
    });
  });

  describe('Status Icons', () => {
    it('should show Loader2 (spinner) icon for connecting status', () => {
      render(<ConnectionStatus status="connecting" />);

      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should show Wifi icon for connected status', () => {
      render(<ConnectionStatus status="connected" />);

      // Wifi icon should be present
      const wifiIcon = document.querySelector('svg.text-green-500');
      expect(wifiIcon).toBeInTheDocument();
    });

    it('should show WifiOff icon for disconnected status', () => {
      render(<ConnectionStatus status="disconnected" />);

      const wifiOffIcon = document.querySelector('svg.text-red-500');
      expect(wifiOffIcon).toBeInTheDocument();
    });

    it('should show WifiOff icon for error status', () => {
      render(<ConnectionStatus status="error" />);

      const wifiOffIcon = document.querySelector('svg.text-red-500');
      expect(wifiOffIcon).toBeInTheDocument();
    });
  });

  describe('Tooltip', () => {
    // Note: JSDOM has limitations with hover events. These tests verify
    // tooltip configuration and visibility toggling.

    it('should NOT show tooltip initially', () => {
      const onRetry = vi.fn();
      render(<ConnectionStatus status="disconnected" onRetry={onRetry} />);

      // Tooltip should not be visible initially
      expect(screen.queryByText('Disconnected')).not.toBeInTheDocument();
      expect(screen.queryByText('Connection lost. Click to retry.')).not.toBeInTheDocument();
    });

    it('should NOT show "Click to reconnect" hint for disabled button', () => {
      // When button is disabled (no onRetry), canRetry is false
      render(<ConnectionStatus status="disconnected" />);

      // The button should be disabled, and "Click to reconnect" shouldn't appear
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      expect(screen.queryByText('Click to reconnect')).not.toBeInTheDocument();
    });

    it('should have correct aria-label with status', () => {
      const { rerender } = render(<ConnectionStatus status="connected" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Connected'
      );

      rerender(<ConnectionStatus status="disconnected" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Disconnected'
      );

      rerender(<ConnectionStatus status="error" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Error'
      );

      rerender(<ConnectionStatus status="connecting" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Connecting'
      );

      rerender(<ConnectionStatus status="disabled" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Offline'
      );
    });
  });

  describe('Click to Retry', () => {
    it('should call onRetry when clicked in disconnected state', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      render(<ConnectionStatus status="disconnected" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should call onRetry when clicked in error state', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      render(<ConnectionStatus status="error" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should call onRetry when clicked in disabled state', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      render(<ConnectionStatus status="disabled" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(onRetry).toHaveBeenCalledTimes(1);
    });

    it('should NOT call onRetry when clicked in connected state', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      render(<ConnectionStatus status="connected" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(onRetry).not.toHaveBeenCalled();
    });

    it('should NOT call onRetry when clicked in connecting state', async () => {
      const user = userEvent.setup();
      const onRetry = vi.fn();

      render(<ConnectionStatus status="connecting" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      await user.click(button);

      expect(onRetry).not.toHaveBeenCalled();
    });

    it('should NOT call anything when onRetry is not provided', async () => {
      const user = userEvent.setup();
      render(<ConnectionStatus status="disconnected" />);

      const button = screen.getByRole('button');

      // Should not throw
      await expect(user.click(button)).resolves.not.toThrow();
    });
  });

  describe('Button State', () => {
    it('should be disabled when status is connected', () => {
      render(<ConnectionStatus status="connected" />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should be disabled when status is connecting', () => {
      render(<ConnectionStatus status="connecting" />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should be enabled when status is disconnected and onRetry provided', () => {
      const onRetry = vi.fn();

      render(<ConnectionStatus status="disconnected" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      expect(button).not.toBeDisabled();
    });

    it('should have hover styling when clickable', () => {
      const onRetry = vi.fn();

      render(<ConnectionStatus status="disconnected" onRetry={onRetry} />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-[#1a1a1a]');
      expect(button).toHaveClass('cursor-pointer');
    });

    it('should have default cursor when not clickable', () => {
      render(<ConnectionStatus status="connected" />);

      const button = screen.getByRole('button');
      expect(button).toHaveClass('cursor-default');
    });
  });

  describe('Accessibility', () => {
    it('should have accessible label describing status', () => {
      render(<ConnectionStatus status="connected" />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label', 'Connection status: Connected');
    });

    it('should update aria-label based on status', () => {
      const { rerender } = render(<ConnectionStatus status="connected" />);

      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Connected'
      );

      rerender(<ConnectionStatus status="disconnected" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Disconnected'
      );

      rerender(<ConnectionStatus status="error" />);
      expect(screen.getByRole('button')).toHaveAttribute(
        'aria-label',
        'Connection status: Error'
      );
    });
  });

  describe('All Status States', () => {
    const statuses: ConnectionState[] = [
      'connected',
      'connecting',
      'disconnected',
      'error',
      'disabled',
    ];

    statuses.forEach((status) => {
      it(`should render without crashing for ${status} status`, () => {
        expect(() => render(<ConnectionStatus status={status} />)).not.toThrow();
      });
    });
  });
});
