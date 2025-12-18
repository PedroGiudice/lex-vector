import React from 'react';
import { X, CheckCircle, XCircle, Info, AlertTriangle } from 'lucide-react';
import { useDocumentStore } from '@/store/documentStore';
import type { Toast as ToastType } from '@/types';
import clsx from 'clsx';

const icons = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
  warning: AlertTriangle,
};

const styles = {
  success: 'bg-gh-accent-success bg-opacity-20 border-gh-accent-success text-gh-accent-success',
  error: 'bg-gh-accent-danger bg-opacity-20 border-gh-accent-danger text-gh-accent-danger',
  info: 'bg-gh-accent-primary bg-opacity-20 border-gh-accent-primary text-gh-accent-primary',
  warning: 'bg-yellow-500 bg-opacity-20 border-yellow-500 text-yellow-500',
};

interface ToastItemProps {
  toast: ToastType;
  onClose: (id: string) => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  const Icon = icons[toast.type];

  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-3 rounded-md border shadow-lg',
        'animate-slide-in-right',
        styles[toast.type]
      )}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="flex-shrink-0 hover:opacity-70 transition-opacity"
        aria-label="Close notification"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useDocumentStore(state => state.toasts);
  const removeToast = useDocumentStore(state => state.removeToast);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {toasts.map(toast => (
        <ToastItem key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>
  );
}

// Add this to your global CSS for the animation
// @keyframes slide-in-right {
//   from {
//     transform: translateX(100%);
//     opacity: 0;
//   }
//   to {
//     transform: translateX(0);
//     opacity: 1;
//   }
// }
