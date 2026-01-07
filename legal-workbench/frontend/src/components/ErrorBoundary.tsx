import * as Sentry from '@sentry/react';
import type { ReactElement, ReactNode } from 'react';

interface ErrorFallbackProps {
  error: Error;
  resetError?: () => void;
}

/**
 * Fallback UI displayed when an error is caught by the ErrorBoundary.
 */
function ErrorFallback({ error, resetError }: ErrorFallbackProps): ReactElement {
  return (
    <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center">
      <div className="max-w-md">
        <h1 className="text-2xl font-bold text-red-600">Algo deu errado</h1>
        <p className="mt-2 text-gray-600">
          Ocorreu um erro inesperado. Nossa equipe foi notificada.
        </p>
        {import.meta.env.DEV && (
          <pre className="mt-4 max-h-32 overflow-auto rounded bg-gray-100 p-2 text-left text-xs text-gray-700">
            {error.message}
          </pre>
        )}
        <div className="mt-6 flex justify-center gap-4">
          <button
            onClick={() => window.location.reload()}
            className="rounded bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
          >
            Recarregar Pagina
          </button>
          {resetError && (
            <button
              onClick={resetError}
              className="rounded border border-gray-300 px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50"
            >
              Tentar Novamente
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactElement;
}

/**
 * Error Boundary component that catches JavaScript errors in child components
 * and reports them to Sentry.
 *
 * @example
 * ```tsx
 * <ErrorBoundary>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
export function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  return (
    <Sentry.ErrorBoundary
      fallback={({ error, resetError }): ReactElement => {
        const errorObj = error instanceof Error ? error : new Error(String(error));
        return fallback ?? <ErrorFallback error={errorObj} resetError={resetError} />;
      }}
      showDialog={import.meta.env.PROD}
      dialogOptions={{
        title: 'Parece que estamos com problemas.',
        subtitle: 'Nossa equipe foi notificada.',
        subtitle2: 'Se quiser ajudar, descreva o que aconteceu abaixo.',
        labelSubmit: 'Enviar',
        labelClose: 'Fechar',
        labelName: 'Nome',
        labelEmail: 'Email',
        labelComments: 'O que aconteceu?',
        successMessage: 'Seu feedback foi enviado. Obrigado!',
      }}
    >
      {children}
    </Sentry.ErrorBoundary>
  );
}
