import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { MatterPreset, MatterPresetInput } from '@/types';

const STORAGE_KEY = 'ledes_matter_presets';

interface MatterPresetsState {
  presets: MatterPreset[];
  selectedPresetId: string | null;

  // Actions
  addPreset: (input: MatterPresetInput) => MatterPreset;
  updatePreset: (id: string, updates: Partial<MatterPresetInput>) => void;
  deletePreset: (id: string) => void;
  selectPreset: (id: string | null) => void;
  getPreset: (id: string) => MatterPreset | undefined;
  getSelectedPreset: () => MatterPreset | undefined;
}

/**
 * Generate a simple unique ID (no external deps needed)
 */
const generateId = (): string =>
  `preset_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

export const useMatterPresetsStore = create<MatterPresetsState>()(
  persist(
    (set, get) => ({
      presets: [],
      selectedPresetId: null,

      addPreset: (input: MatterPresetInput): MatterPreset => {
        const now = new Date().toISOString();
        const newPreset: MatterPreset = {
          ...input,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        };

        set((state) => ({
          presets: [...state.presets, newPreset],
        }));

        return newPreset;
      },

      updatePreset: (id: string, updates: Partial<MatterPresetInput>) => {
        set((state) => ({
          presets: state.presets.map((preset) =>
            preset.id === id
              ? { ...preset, ...updates, updatedAt: new Date().toISOString() }
              : preset
          ),
        }));
      },

      deletePreset: (id: string) => {
        set((state) => ({
          presets: state.presets.filter((preset) => preset.id !== id),
          selectedPresetId: state.selectedPresetId === id ? null : state.selectedPresetId,
        }));
      },

      selectPreset: (id: string | null) => {
        set({ selectedPresetId: id });
      },

      getPreset: (id: string): MatterPreset | undefined => {
        return get().presets.find((preset) => preset.id === id);
      },

      getSelectedPreset: (): MatterPreset | undefined => {
        const { presets, selectedPresetId } = get();
        return selectedPresetId ? presets.find((p) => p.id === selectedPresetId) : undefined;
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        presets: state.presets,
        // Don't persist selectedPresetId - user should re-select each session
      }),
    }
  )
);
