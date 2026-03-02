/**
 * Hook para persistencia key-value usando tauri-plugin-store.
 * Fallback para localStorage quando rodando no browser (dev mode).
 */
import { useState, useEffect, useCallback, useRef } from "react";

const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

let storeInstance: any = null;

async function getStore() {
  if (!isTauri) return null;
  if (storeInstance) return storeInstance;
  const { LazyStore } = await import("@tauri-apps/plugin-store");
  storeInstance = new LazyStore("settings.json");
  return storeInstance;
}

/**
 * useTauriStore<T>(key, defaultValue)
 *
 * Retorna [value, setValue] similar a useState, mas persistido.
 * No Tauri: usa plugin-store. No browser: usa localStorage.
 */
export function useTauriStore<T extends string>(
  key: string,
  defaultValue: T,
): [T, (val: T) => void] {
  const [value, setValue] = useState<T>(() => {
    if (!isTauri) {
      const saved = localStorage.getItem(key);
      return (saved as T) ?? defaultValue;
    }
    return defaultValue;
  });

  const initialized = useRef(false);

  // Carregar valor do store Tauri na montagem
  useEffect(() => {
    if (!isTauri) {
      initialized.current = true;
      return;
    }
    let cancelled = false;
    getStore().then(async (store) => {
      if (!store || cancelled) return;
      const saved = (await store.get(key)) as T | undefined;
      if (!cancelled && saved !== undefined && saved !== null) {
        setValue(saved as T);
      }
      initialized.current = true;
    });
    return () => { cancelled = true; };
  }, [key]);

  const update = useCallback(
    (newVal: T) => {
      setValue(newVal);
      if (isTauri) {
        getStore().then(async (store) => {
          if (!store) return;
          await store.set(key, newVal);
          await store.save();
        });
      } else {
        localStorage.setItem(key, newVal);
      }
    },
    [key],
  );

  return [value, update];
}
