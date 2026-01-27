import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { initSentry } from './lib/sentry';
import { router } from './routes';
import { UpdateBanner } from './components/UpdateBanner';
import './index.css';

// Initialize Sentry before rendering the app
initSentry();

// TanStack Query client - required for Tauri data fetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 min
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <UpdateBanner />
    </QueryClientProvider>
  </React.StrictMode>
);
