import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { DownloadPanel } from '@/components/stj/DownloadPanel';
import { useSTJStore } from '@/store/stjStore';

// Mock the store
vi.mock('@/store/stjStore');

const mockUseSTJStore = useSTJStore as Mock;

// Default mock stats for dynamic orgao list
const mockStats = {
  total_acordaos: 1000,
  por_orgao: {
    'PRIMEIRA TURMA': 150,
    'SEGUNDA TURMA': 130,
    'TERCEIRA TURMA': 120,
    'QUARTA TURMA': 110,
    'QUINTA TURMA': 100,
    'SEXTA TURMA': 90,
    'PRIMEIRA SECAO': 80,
    'SEGUNDA SECAO': 70,
    'TERCEIRA SECAO': 60,
    'CORTE ESPECIAL': 50,
  },
  por_tipo: {},
  ultimos_30_dias: 100,
};

// Default mock state
const createMockState = (overrides = {}) => ({
  syncStatus: 'idle' as const,
  isSyncing: false,
  syncProgress: {
    downloaded: 0,
    processed: 0,
    inserted: 0,
    duplicates: 0,
    errors: 0,
  },
  syncError: null,
  startSync: vi.fn(),
  cancelSync: vi.fn(),
  resetSyncState: vi.fn(),
  stats: mockStats,
  loadStats: vi.fn(),
  ...overrides,
});

describe('DownloadPanel Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseSTJStore.mockReturnValue(createMockState());
  });

  describe('Rendering', () => {
    it('renders the component with title', () => {
      render(<DownloadPanel />);
      expect(screen.getByText('Download Massivo')).toBeInTheDocument();
    });

    it('renders all period options', () => {
      render(<DownloadPanel />);
      expect(screen.getByLabelText(/Ultimos 30 dias/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Ultimos 90 dias/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Ultimos 365 dias/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Desde 2022/)).toBeInTheDocument();
      expect(screen.getByLabelText(/Periodo personalizado/)).toBeInTheDocument();
    });

    it('renders the start download button when idle', () => {
      render(<DownloadPanel />);
      expect(screen.getByRole('button', { name: /Iniciar Download/i })).toBeInTheDocument();
    });

    it('renders orgao filter toggle button', () => {
      render(<DownloadPanel />);
      expect(screen.getByText(/Filtrar por orgao/i)).toBeInTheDocument();
    });

    it('applies custom className', () => {
      const { container } = render(<DownloadPanel className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Period Selection', () => {
    it('selects 30 days by default', () => {
      render(<DownloadPanel />);
      const radio = screen.getByRole('radio', { name: /Ultimos 30 dias/i });
      expect(radio).toBeChecked();
    });

    it('allows changing period selection', () => {
      render(<DownloadPanel />);
      const radio90 = screen.getByRole('radio', { name: /Ultimos 90 dias/i });
      fireEvent.click(radio90);
      expect(radio90).toBeChecked();
    });

    it('shows custom date pickers when custom period is selected', () => {
      render(<DownloadPanel />);
      const customRadio = screen.getByRole('radio', { name: /Periodo personalizado/i });
      fireEvent.click(customRadio);

      expect(screen.getByLabelText(/Data inicio/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Data fim/i)).toBeInTheDocument();
    });

    it('hides custom date pickers when preset period is selected', () => {
      render(<DownloadPanel />);

      // First show custom dates
      fireEvent.click(screen.getByRole('radio', { name: /Periodo personalizado/i }));
      expect(screen.getByLabelText(/Data inicio/i)).toBeInTheDocument();

      // Then select preset
      fireEvent.click(screen.getByRole('radio', { name: /Ultimos 30 dias/i }));
      expect(screen.queryByLabelText(/Data inicio/i)).not.toBeInTheDocument();
    });
  });

  describe('Orgao Filter', () => {
    it('toggles orgao filter section visibility', () => {
      render(<DownloadPanel />);
      const toggleButton = screen.getByText(/Filtrar por orgao/i);

      // Initially hidden - look for text containing "PRIMEIRA TURMA" (with count)
      expect(screen.queryByText(/PRIMEIRA TURMA/)).not.toBeInTheDocument();

      // Click to show
      fireEvent.click(toggleButton);
      expect(screen.getByText(/PRIMEIRA TURMA \(150\)/)).toBeInTheDocument();

      // Click to hide
      fireEvent.click(toggleButton);
      expect(screen.queryByText(/PRIMEIRA TURMA/)).not.toBeInTheDocument();
    });

    it('allows selecting multiple orgaos', () => {
      render(<DownloadPanel />);
      fireEvent.click(screen.getByText(/Filtrar por orgao/i));

      const checkbox1 = screen.getByRole('checkbox', { name: /PRIMEIRA TURMA/i });
      const checkbox2 = screen.getByRole('checkbox', { name: /SEGUNDA TURMA/i });

      fireEvent.click(checkbox1);
      fireEvent.click(checkbox2);

      expect(checkbox1).toBeChecked();
      expect(checkbox2).toBeChecked();
    });

    it('shows count of selected orgaos', () => {
      render(<DownloadPanel />);
      fireEvent.click(screen.getByText(/Filtrar por orgao/i));

      fireEvent.click(screen.getByRole('checkbox', { name: /PRIMEIRA TURMA/i }));
      fireEvent.click(screen.getByRole('checkbox', { name: /SEGUNDA TURMA/i }));

      expect(screen.getByText(/2 selecionados/)).toBeInTheDocument();
    });
  });

  describe('Download Actions', () => {
    it('calls startSync when clicking start button', async () => {
      const startSync = vi.fn();
      mockUseSTJStore.mockReturnValue(createMockState({ startSync }));

      render(<DownloadPanel />);
      fireEvent.click(screen.getByRole('button', { name: /Iniciar Download/i }));

      expect(startSync).toHaveBeenCalledWith({
        period: '30',
      });
    });

    it('includes selected orgaos in sync params', async () => {
      const startSync = vi.fn();
      mockUseSTJStore.mockReturnValue(createMockState({ startSync }));

      render(<DownloadPanel />);

      // Open and select orgaos
      fireEvent.click(screen.getByText(/Filtrar por orgao/i));
      fireEvent.click(screen.getByRole('checkbox', { name: /Primeira Turma/i }));

      // Start download
      fireEvent.click(screen.getByRole('button', { name: /Iniciar Download/i }));

      expect(startSync).toHaveBeenCalledWith({
        period: '30',
        orgaos: ['PRIMEIRA TURMA'],
      });
    });

    it('includes custom dates in sync params', async () => {
      const startSync = vi.fn();
      mockUseSTJStore.mockReturnValue(createMockState({ startSync }));

      render(<DownloadPanel />);

      // Select custom period
      fireEvent.click(screen.getByRole('radio', { name: /Periodo personalizado/i }));

      // Set dates
      fireEvent.change(screen.getByLabelText(/Data inicio/i), {
        target: { value: '2024-01-01' },
      });
      fireEvent.change(screen.getByLabelText(/Data fim/i), {
        target: { value: '2024-06-30' },
      });

      // Start download
      fireEvent.click(screen.getByRole('button', { name: /Iniciar Download/i }));

      expect(startSync).toHaveBeenCalledWith({
        period: 'custom',
        dataInicio: '2024-01-01',
        dataFim: '2024-06-30',
      });
    });

    it('disables start button when custom dates are incomplete', () => {
      render(<DownloadPanel />);

      // Select custom period
      fireEvent.click(screen.getByRole('radio', { name: /Periodo personalizado/i }));

      // Only set start date
      fireEvent.change(screen.getByLabelText(/Data inicio/i), {
        target: { value: '2024-01-01' },
      });

      const startButton = screen.getByRole('button', { name: /Iniciar Download/i });
      expect(startButton).toBeDisabled();
    });
  });

  describe('Syncing State', () => {
    it('shows cancel button when syncing', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'downloading',
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByRole('button', { name: /Cancelar/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Iniciar Download/i })).not.toBeInTheDocument();
    });

    it('calls cancelSync when clicking cancel button', () => {
      const cancelSync = vi.fn();
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'downloading',
          cancelSync,
        })
      );

      render(<DownloadPanel />);
      fireEvent.click(screen.getByRole('button', { name: /Cancelar/i }));
      expect(cancelSync).toHaveBeenCalled();
    });

    it('disables period selection while syncing', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'downloading',
        })
      );

      render(<DownloadPanel />);
      const radios = screen.getAllByRole('radio');
      radios.forEach((radio) => {
        expect(radio).toBeDisabled();
      });
    });

    it('shows progress stats when syncing', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'downloading',
          syncProgress: {
            downloaded: 100,
            processed: 80,
            inserted: 75,
            duplicates: 5,
            errors: 0,
          },
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('80')).toBeInTheDocument();
      expect(screen.getByText('75')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('shows progress bar with percentage', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'downloading',
          syncProgress: {
            downloaded: 50,
            processed: 50,
            inserted: 50,
            duplicates: 0,
            errors: 0,
            percent: 50,
          },
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByText('50.0%')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50');
    });
  });

  describe('Status Display', () => {
    it('shows downloading status', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'downloading',
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByText('Baixando dados...')).toBeInTheDocument();
    });

    it('shows processing status', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          isSyncing: true,
          syncStatus: 'processing',
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByText('Processando...')).toBeInTheDocument();
    });

    it('shows complete status with reset button', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          syncStatus: 'complete',
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByText('Concluido!')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Nova Sincronizacao/i })).toBeInTheDocument();
    });

    it('shows error status with message', () => {
      mockUseSTJStore.mockReturnValue(
        createMockState({
          syncStatus: 'error',
          syncError: 'Erro de conexao',
        })
      );

      render(<DownloadPanel />);
      expect(screen.getByText('Erro')).toBeInTheDocument();
      expect(screen.getByText('Erro de conexao')).toBeInTheDocument();
    });

    it('calls resetSyncState when clicking reset button', () => {
      const resetSyncState = vi.fn();
      mockUseSTJStore.mockReturnValue(
        createMockState({
          syncStatus: 'complete',
          resetSyncState,
        })
      );

      render(<DownloadPanel />);
      fireEvent.click(screen.getByRole('button', { name: /Nova Sincronizacao/i }));
      expect(resetSyncState).toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('has proper region role and label', () => {
      render(<DownloadPanel />);
      expect(screen.getByRole('region', { name: /Download Massivo/i })).toBeInTheDocument();
    });

    it('has proper radiogroup for period selection', () => {
      render(<DownloadPanel />);
      expect(screen.getByRole('radiogroup', { name: /Selecionar periodo/i })).toBeInTheDocument();
    });

    it('has aria-live for status updates', () => {
      render(<DownloadPanel />);
      const statusRegion = screen.getByRole('status');
      expect(statusRegion).toHaveAttribute('aria-live', 'polite');
    });

    it('has proper aria-expanded for orgao filter toggle', () => {
      render(<DownloadPanel />);
      const toggleButton = screen.getByRole('button', { name: /Filtrar por orgao/i });
      expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

      fireEvent.click(toggleButton);
      expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    });
  });
});
