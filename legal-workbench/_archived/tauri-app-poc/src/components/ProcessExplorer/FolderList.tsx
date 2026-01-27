import { ProcessFolder } from '../../hooks/useTauri';

interface Props {
  folders: ProcessFolder[];
  selectedFolder: ProcessFolder | null;
  onSelectFolder: (folder: ProcessFolder) => void;
}

export function FolderList({ folders, selectedFolder, onSelectFolder }: Props) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div style={{ flex: 1, overflow: 'auto' }}>
      {folders.map((folder) => (
        <button
          key={folder.path}
          onClick={() => onSelectFolder(folder)}
          style={{
            width: '100%',
            padding: '12px',
            textAlign: 'left',
            background: selectedFolder?.path === folder.path ? '#eff6ff' : 'transparent',
            border: 'none',
            borderBottom: '1px solid #e5e7eb',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}
        >
          <span style={{ fontSize: '20px' }}>folder</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontWeight: 500, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{folder.name}</p>
            <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
              {folder.pdf_count} PDFs - {formatSize(folder.total_size_bytes)}
            </p>
          </div>
        </button>
      ))}
    </div>
  );
}
