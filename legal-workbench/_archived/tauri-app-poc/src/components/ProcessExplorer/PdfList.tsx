import { PdfFile } from '../../hooks/useTauri';

interface Props {
  pdfs: PdfFile[];
  folderName: string;
}

export function PdfList({ pdfs, folderName }: Props) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusIcon = (status: PdfFile['extraction_status']) => {
    if (status === 'Completed') return '[ok]';
    if (status === 'InProgress') return '[...]';
    if (status === 'Pending') return '[ ]';
    return '[x]';
  };

  const getStatusColor = (status: PdfFile['extraction_status']) => {
    if (status === 'Completed') return '#22c55e';
    if (status === 'InProgress') return '#eab308';
    if (status === 'Pending') return '#9ca3af';
    return '#ef4444';
  };

  return (
    <div style={{ padding: '16px' }}>
      <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px' }}>{folderName}</h2>
      <p style={{ color: '#6b7280', marginBottom: '16px' }}>{pdfs.length} arquivos PDF</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {pdfs.map((pdf) => (
          <div
            key={pdf.path}
            style={{
              padding: '12px',
              backgroundColor: 'white',
              borderRadius: '4px',
              border: '1px solid #e5e7eb',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}
          >
            <span style={{ fontSize: '20px', color: '#ef4444' }}>PDF</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{ fontWeight: 500, margin: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{pdf.name}</p>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>{formatSize(pdf.size_bytes)}</p>
            </div>
            <span style={{ color: getStatusColor(pdf.extraction_status), fontSize: '16px' }}>
              {getStatusIcon(pdf.extraction_status)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
