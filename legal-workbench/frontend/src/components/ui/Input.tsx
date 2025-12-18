import React from 'react';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-gh-text-primary mb-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-3 py-2 bg-gh-bg-tertiary border border-gh-border-default rounded-md',
            'text-gh-text-primary placeholder-gh-text-secondary',
            'focus:outline-none focus:ring-2 focus:ring-gh-accent-primary focus:border-transparent',
            'transition-colors',
            error && 'border-gh-accent-danger focus:ring-gh-accent-danger',
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-sm text-gh-accent-danger">{error}</p>}
        {helperText && !error && (
          <p className="mt-1 text-sm text-gh-text-secondary">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
