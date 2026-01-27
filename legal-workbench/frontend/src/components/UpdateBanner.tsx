import { useAutoUpdate } from '@/hooks/useAutoUpdate';

export function UpdateBanner() {
  const { updateInfo, downloadAndInstall } = useAutoUpdate();

  if (!updateInfo) return null;

  return (
    <div className="fixed bottom-4 right-4 bg-accent-indigo text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-3 z-50">
      <span className="text-sm">v{updateInfo.version} disponivel</span>
      <button
        onClick={downloadAndInstall}
        className="bg-white text-accent-indigo px-3 py-1 rounded text-sm font-medium hover:bg-gray-100"
      >
        Atualizar
      </button>
    </div>
  );
}
