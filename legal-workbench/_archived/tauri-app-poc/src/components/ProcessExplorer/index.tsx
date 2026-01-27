import { useState } from 'react';
import { useTauri, ProcessFolder, PdfFile } from '../../hooks/useTauri';
import { FolderList } from './FolderList';
import { PdfList } from './PdfList';

export function ProcessExplorer() {
  const { selectFolder, listProcessFolders, listPdfs, loading, error } = useTauri();
  const [rootPath, setRootPath] = useState<string | null>(null);
  const [folders, setFolders] = useState<ProcessFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<ProcessFolder | null>(null);
  const [pdfs, setPdfs] = useState<PdfFile[]>([]);

  const handleSelectRoot = async () => {
    const path = await selectFolder();
    if (path) {
      setRootPath(path);
      const folders = await listProcessFolders(path);
      setFolders(folders);
      setSelectedFolder(null);
      setPdfs([]);
    }
  };

  const handleSelectFolder = async (folder: ProcessFolder) => {
    setSelectedFolder(folder);
    const pdfs = await listPdfs(folder.path);
    setPdfs(pdfs);
  };

  return (
    <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f9fafb' }}>
      {/* Sidebar */}
      <div style={{ width: '320px', backgroundColor: 'white', borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #e5e7eb' }}>
          <button
            onClick={handleSelectRoot}
            style={{
              width: '100%',
              padding: '8px 16px',
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Selecionar Pasta Raiz
          </button>
          {rootPath && (
            <p style={{ marginTop: '8px', fontSize: '14px', color: '#6b7280', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{rootPath}</p>
          )}
        </div>
        <FolderList
          folders={folders}
          selectedFolder={selectedFolder}
          onSelectFolder={handleSelectFolder}
        />
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {error && (
          <div style={{ margin: '16px', padding: '16px', backgroundColor: '#fee2e2', color: '#dc2626', borderRadius: '4px' }}>{error}</div>
        )}
        {loading && (
          <div style={{ margin: '16px', padding: '16px', color: '#6b7280' }}>Carregando...</div>
        )}
        {selectedFolder && <PdfList pdfs={pdfs} folderName={selectedFolder.name} />}
        {!selectedFolder && !loading && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#9ca3af' }}>
            Selecione uma pasta de processo
          </div>
        )}
      </div>
    </div>
  );
}
