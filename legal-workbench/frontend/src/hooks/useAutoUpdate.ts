/**
 * Auto-update hook for Tauri desktop app
 * Checks for updates and provides install functionality
 */

import { useState, useEffect, useCallback } from 'react';
import { isTauri } from '@/lib/tauri';

export interface UpdateInfo {
  version: string;
  date: string;
  body: string;
}

export interface UseAutoUpdateReturn {
  isAvailable: boolean;
  isChecking: boolean;
  updateInfo: UpdateInfo | null;
  error: string | null;
  checkForUpdates: () => Promise<void>;
  downloadAndInstall: () => Promise<void>;
}

export function useAutoUpdate(): UseAutoUpdateReturn {
  const [isChecking, setIsChecking] = useState(false);
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isAvailable = isTauri();

  const checkForUpdates = useCallback(async () => {
    if (!isAvailable) return;

    setIsChecking(true);
    setError(null);

    try {
      const { check } = await import('@tauri-apps/plugin-updater');
      const update = await check();

      if (update) {
        setUpdateInfo({
          version: update.version,
          date: update.date ?? '',
          body: update.body ?? '',
        });
        // Show native notification
        try {
          const { sendNotification } = await import('@tauri-apps/plugin-notification');
          sendNotification({
            title: 'Atualizacao disponivel',
            body: `Legal Workbench v${update.version} esta disponivel. Reinicie para atualizar.`,
          });
        } catch {
          // Notification permission may not be granted
        }
      } else {
        setUpdateInfo(null);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao verificar atualizacoes';
      setError(message);
      console.error('Update check error:', err);
    } finally {
      setIsChecking(false);
    }
  }, [isAvailable]);

  const downloadAndInstall = useCallback(async () => {
    if (!isAvailable || !updateInfo) return;

    try {
      const { check } = await import('@tauri-apps/plugin-updater');
      const { relaunch } = await import('@tauri-apps/plugin-process');

      const update = await check();
      if (update) {
        // Download and install
        await update.downloadAndInstall();
        // Restart the app
        await relaunch();
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Erro ao instalar atualizacao';
      setError(message);
      console.error('Update install error:', err);
    }
  }, [isAvailable, updateInfo]);

  // Check for updates on mount (only in Tauri)
  useEffect(() => {
    if (isAvailable) {
      // Delay initial check to not block app startup
      const timer = setTimeout(() => {
        checkForUpdates();
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [isAvailable, checkForUpdates]);

  return {
    isAvailable,
    isChecking,
    updateInfo,
    error,
    checkForUpdates,
    downloadAndInstall,
  };
}
