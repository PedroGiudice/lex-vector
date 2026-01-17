import * as Sentry from '@sentry/react';

/**
 * Initialize Sentry for error tracking and performance monitoring.
 * Only initializes if VITE_SENTRY_DSN is configured.
 * Disabled in development mode by default.
 */
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN;

  if (!dsn) {
    if (import.meta.env.DEV) {
      console.log('[Sentry] DSN not configured, skipping initialization');
    }
    return;
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.MODE,
    release: import.meta.env.VITE_APP_VERSION || undefined,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
      // Send console.log, console.warn, and console.error as logs to Sentry
      Sentry.consoleLoggingIntegration({ levels: ['log', 'warn', 'error'] }),
    ],
    // Enable logs to be sent to Sentry
    _experiments: {
      enableLogs: true,
    },
    // Performance Monitoring
    tracesSampleRate: import.meta.env.MODE === 'production' ? 0.1 : 1.0,
    // Session Replay
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    // Disable in development unless explicitly enabled
    enabled: import.meta.env.MODE !== 'development',
    // Filter out common non-actionable errors
    beforeSend(event) {
      // Don't send events for network errors that are likely transient
      if (event.exception?.values?.[0]?.type === 'ChunkLoadError') {
        return null;
      }
      return event;
    },
  });
}

export { Sentry };
