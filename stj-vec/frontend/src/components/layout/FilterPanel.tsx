import { useFilters } from '@/hooks/use-filters.ts';
import { useAppStore } from '@/store/app-store.ts';
import type { SearchFilters } from '@/api/types.ts';

const selectStyle: React.CSSProperties = {
  background: 'var(--color-bg-input)',
  border: '1px solid var(--color-border-card)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--color-text-primary)',
  fontSize: 12,
  padding: '4px 8px',
  minWidth: 120,
  maxWidth: 180,
  outline: 'none',
  fontFamily: 'inherit',
};

const dateStyle: React.CSSProperties = {
  ...selectStyle,
  minWidth: 100,
  maxWidth: 130,
  colorScheme: 'dark',
};

const labelStyle: React.CSSProperties = {
  fontSize: 10,
  fontWeight: 600,
  color: 'var(--color-text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  marginBottom: 2,
};

export const FilterPanel: React.FC = () => {
  const { data } = useFilters();
  const filters = useAppStore((s) => s.filters);
  const setFilter = useAppStore((s) => s.setFilter);
  const clearFilters = useAppStore((s) => s.clearFilters);

  const hasActiveFilters = Object.values(filters).some(Boolean);

  const renderSelect = (
    label: string,
    key: keyof SearchFilters,
    options: string[] | undefined,
  ) => (
    <div className="flex flex-col">
      <span style={labelStyle}>{label}</span>
      <select
        style={selectStyle}
        value={filters[key] ?? ''}
        onChange={(e) => setFilter(key, e.target.value || undefined)}
      >
        <option value="">Todos</option>
        {options?.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </div>
  );

  return (
    <div
      className="flex items-end gap-3 flex-wrap"
      style={{
        padding: '8px 16px',
        borderBottom: '1px solid var(--color-border-subtle)',
        background: 'var(--color-bg-surface)',
      }}
    >
      {renderSelect('Ministro', 'ministro', data?.ministros)}
      {renderSelect('Tipo', 'tipo', data?.tipos)}
      {renderSelect('Classe', 'classe', data?.classes)}
      {renderSelect('Orgao Julgador', 'orgao_julgador', data?.orgaos_julgadores)}

      <div className="flex flex-col">
        <span style={labelStyle}>De</span>
        <input
          type="date"
          style={dateStyle}
          value={filters.data_from ?? ''}
          onChange={(e) => setFilter('data_from', e.target.value || undefined)}
        />
      </div>

      <div className="flex flex-col">
        <span style={labelStyle}>Ate</span>
        <input
          type="date"
          style={dateStyle}
          value={filters.data_to ?? ''}
          onChange={(e) => setFilter('data_to', e.target.value || undefined)}
        />
      </div>

      {hasActiveFilters && (
        <button
          onClick={clearFilters}
          style={{
            fontSize: 11,
            color: 'var(--color-accent)',
            background: 'var(--color-accent-soft)',
            border: '1px solid var(--color-accent)',
            borderRadius: 'var(--radius-sm)',
            padding: '4px 10px',
            cursor: 'pointer',
            fontWeight: 500,
            marginBottom: 1,
          }}
        >
          Limpar filtros
        </button>
      )}
    </div>
  );
};

export default FilterPanel;
