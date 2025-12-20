import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import CodeBlock from './CodeBlock';

describe('CodeBlock', () => {
  let mockClipboard;

  beforeEach(() => {
    // Mock clipboard API
    mockClipboard = {
      writeText: vi.fn(() => Promise.resolve()),
    };
    Object.assign(navigator, {
      clipboard: mockClipboard,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Inline Code', () => {
    it('renders inline code with correct styling', () => {
      render(
        <CodeBlock inline>npm install</CodeBlock>
      );

      const code = screen.getByText('npm install');
      expect(code.tagName).toBe('CODE');
      expect(code.className).toContain('font-mono');
      expect(code.className).toContain('px-1.5');
      expect(code.className).toContain('py-0.5');
    });

    it('renders single-line code as inline by default', () => {
      render(
        <CodeBlock>const x = 5;</CodeBlock>
      );

      const code = screen.getByText('const x = 5;');
      expect(code.tagName).toBe('CODE');
      expect(code.className).toContain('font-mono');
    });

    it('detects inlineCode node type', () => {
      const mockNode = { type: 'inlineCode' };
      render(
        <CodeBlock node={mockNode}>inline code</CodeBlock>
      );

      const code = screen.getByText('inline code');
      expect(code.tagName).toBe('CODE');
      expect(code.className).toContain('font-mono');
    });
  });

  describe('Block Code', () => {
    it('renders multiline code as block', () => {
      const code = 'const greeting = "Hello";\nconsole.log(greeting);';
      render(<CodeBlock>{code}</CodeBlock>);

      const pre = screen.getByText(code).closest('pre');
      expect(pre).toBeInTheDocument();
      expect(pre.className).toContain('bg-gray-900');
      expect(pre.className).toContain('rounded-lg');
    });

    it('displays copy button on render', () => {
      render(
        <CodeBlock>const x = 1;\nconst y = 2;</CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      expect(copyButton).toBeInTheDocument();
    });

    it('copies code to clipboard when copy button is clicked', async () => {
      const code = 'const x = 1;\nconst y = 2;';
      render(<CodeBlock>{code}</CodeBlock>);

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      fireEvent.click(copyButton);

      expect(mockClipboard.writeText).toHaveBeenCalledWith(code);

      await waitFor(() => {
        expect(screen.getByText('Copied')).toBeInTheDocument();
      });
    });

    it('shows "Copied" feedback for 1.5 seconds', async () => {
      vi.useFakeTimers();

      render(
        <CodeBlock>const x = 1;</CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(screen.getByText('Copied')).toBeInTheDocument();
      });

      // Fast-forward time
      vi.advanceTimersByTime(1500);

      await waitFor(() => {
        expect(screen.queryByText('Copied')).not.toBeInTheDocument();
      });

      vi.useRealTimers();
    });

    it('extracts and displays language from className', () => {
      render(
        <CodeBlock className="language-javascript">
          const x = 1;{'\n'}const y = 2;
        </CodeBlock>
      );

      expect(screen.getByText('javascript')).toBeInTheDocument();
    });

    it('handles array children', () => {
      const children = ['const x = 1;', '\n', 'const y = 2;'];
      render(<CodeBlock>{children}</CodeBlock>);

      const code = screen.getByText('const x = 1;\nconst y = 2;');
      expect(code).toBeInTheDocument();
    });

    it('falls back to execCommand when clipboard API fails', async () => {
      // Mock clipboard to fail
      mockClipboard.writeText = vi.fn(() => Promise.reject(new Error('Clipboard failed')));

      // Mock execCommand
      const execCommandSpy = vi.spyOn(document, 'execCommand').mockImplementation(() => true);

      const code = 'const x = 1;';
      render(<CodeBlock>{code}</CodeBlock>);

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(execCommandSpy).toHaveBeenCalledWith('copy');
      });

      execCommandSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('has proper aria-label on copy button', () => {
      render(
        <CodeBlock>const x = 1;\nconst y = 2;</CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      expect(copyButton).toHaveAttribute('aria-label', 'Copy code');
    });

    it('updates aria-label after copy', async () => {
      render(
        <CodeBlock>const x = 1;\nconst y = 2;</CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      fireEvent.click(copyButton);

      await waitFor(() => {
        expect(copyButton).toHaveAttribute('aria-label', 'Copied');
      });
    });

    it('has proper title attribute on copy button', () => {
      render(
        <CodeBlock>const x = 1;\nconst y = 2;</CodeBlock>
      );

      const copyButton = screen.getByRole('button', { name: /copy code/i });
      expect(copyButton).toHaveAttribute('title', 'Copy code');
    });
  });

  describe('Styling', () => {
    it('applies custom className to inline code', () => {
      render(
        <CodeBlock inline className="custom-class">test</CodeBlock>
      );

      const code = screen.getByText('test');
      expect(code.className).toContain('custom-class');
    });

    it('applies custom className to block code', () => {
      render(
        <CodeBlock className="language-python">
          def hello():{'\n'}    print("Hello")
        </CodeBlock>
      );

      const code = screen.getByText(/def hello/).closest('code');
      expect(code.className).toContain('language-python');
    });

    it('applies group hover class for copy button visibility', () => {
      render(
        <CodeBlock>const x = 1;\nconst y = 2;</CodeBlock>
      );

      const container = screen.getByRole('button').closest('.group');
      expect(container.className).toContain('group');
    });
  });
});
