import React, { useState } from 'react';
import useTrelloStore from '@/store/trelloStore';
import * as trelloApi from '@/services/trelloApi';
import { Download, Copy, Plus, Archive, Trash2, Link, ListChecks, Tag, Box } from 'lucide-react';

export function ActionsPanel() {
  const {
    selectedCardIds,
    selectedBoardId,
    createCard,
    isLoading,
    cards,
    lists,
    labels,
    members,
    clearCardSelection,
    archiveSelectedCards,
    deleteSelectedCards,
    toggleMoveCardsModal,
    toggleBulkLabelModal,
  } = useTrelloStore();

  const [exportFormat, setExportFormat] = useState<'json' | 'csv' | 'markdown' | 'text'>('json');

  const numSelected = selectedCardIds.size;
  const hasSelection = numSelected > 0;
  const singleSelected = numSelected === 1;

  const selectedCard = singleSelected
    ? cards.find(c => selectedCardIds.has(c.id))
    : null;

  const handleCreateCard = async () => {
    if (selectedBoardId) {
      const firstList = useTrelloStore.getState().lists[0];
      if (firstList) {
        const cardName = prompt('Enter new card name:');
        if (cardName) {
          await createCard({ idList: firstList.id, name: cardName });
        }
      } else {
        alert('Please create a list first or select a board with lists.');
      }
    } else {
      alert('Please select a board first.');
    }
  };

  const handleArchiveSelected = async () => {
    if (hasSelection && confirm(`Archive ${numSelected} card(s)?`)) {
      await archiveSelectedCards();
      clearCardSelection();
    }
  };

  const handleDeleteSelected = async () => {
    if (hasSelection && confirm(`⚠️ PERMANENTLY DELETE ${numSelected} card(s)? This cannot be undone!`)) {
      await deleteSelectedCards();
      clearCardSelection();
    }
  };

  const handleExport = async (format: 'json' | 'csv' | 'markdown' | 'text') => {
    const dataToExport = hasSelection
      ? cards.filter(card => selectedCardIds.has(card.id))
      : cards;

    if (dataToExport.length === 0) {
      alert('No data to export.');
      return;
    }
    try {
      await trelloApi.exportData(dataToExport, format, `trello-export-${Date.now()}`, lists, labels, members);
    } catch (error) {
      console.error("Export failed:", error);
      alert(`Failed to export data: ${(error as Error).message}`);
    }
  };

  const handleCopy = async () => {
    const dataToCopy = hasSelection
      ? cards.filter(card => selectedCardIds.has(card.id))
      : cards;

    if (dataToCopy.length === 0) {
      alert('No data to copy.');
      return;
    }

    try {
      await trelloApi.copyToClipboard(dataToCopy, exportFormat, lists, labels, members);
      alert(`Copied ${dataToCopy.length} card(s) as ${exportFormat.toUpperCase()}`);
    } catch (error) {
      console.error("Copy to clipboard failed:", error);
      alert(`Failed to copy to clipboard. Please ensure browser permissions are granted. Error: ${(error as Error).message}`);
    }
  };

  const handleOpenInTrello = () => {
    if (selectedCard?.shortUrl) {
      window.open(selectedCard.shortUrl, '_blank');
    }
  };

  return (
    <aside className="w-1/4 bg-bg-panel-1 border-l border-border-default flex flex-col p-4 overflow-y-auto text-text-primary text-xs animate-in fade-in slide-in-from-right-2 duration-200">

      {/* ========== EXPORT SECTION (PRIMARY FOCUS) ========== */}
      <h3 className="text-accent-indigo uppercase font-semibold text-xxs tracking-wider mb-4 border-b border-accent-indigo/50 pb-2 flex items-center gap-2">
        <Download size={14} className="text-accent-indigo"/> Extract Data <span className="text-text-muted font-mono ml-auto">({hasSelection ? `${numSelected} selected` : 'all visible'})</span>
      </h3>

      <div className="space-y-4 mb-6">
        {/* Format selector */}
        <div>
          <label className="text-text-muted text-xxs block mb-1.5">Format:</label>
          <select
            className="w-full bg-bg-input text-text-primary py-2.5 px-3 rounded-sm border border-border-default text-xs focus:outline-none focus:ring-1 focus:ring-accent-indigo transition-colors appearance-none"
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as any)}
            disabled={isLoading || cards.length === 0}
          >
            <option value="json">JSON (structured)</option>
            <option value="csv">CSV (spreadsheet)</option>
            <option value="markdown">Markdown (docs)</option>
            <option value="text">Plain Text</option>
          </select>
        </div>

        {/* Export actions */}
        <div className="flex space-x-2">
          <button
            className="flex-1 bg-accent-indigo hover:bg-accent-indigo-light text-white font-semibold py-2.5 px-3 rounded-sm text-xs transition-all active:scale-95 flex items-center justify-center gap-2"
            onClick={handleCopy}
            disabled={isLoading || cards.length === 0}
          >
            <Copy size={14}/> Copy
          </button>
          <button
            className="flex-1 bg-bg-input hover:bg-border-light text-text-primary font-semibold py-2.5 px-3 rounded-sm text-xs transition-all border border-border-default active:scale-95 flex items-center justify-center gap-2"
            onClick={() => handleExport(exportFormat)}
            disabled={isLoading || cards.length === 0}
          >
            <Download size={14}/> Download
          </button>
        </div>

        {/* Quick export buttons */}
        <div className="flex flex-wrap gap-1.5">
          <button
            className="px-2.5 py-1.5 bg-bg-input hover:bg-border-light text-text-secondary rounded-sm text-xxs border border-border-default transition-colors active:scale-95"
            onClick={() => handleExport('json')}
            disabled={isLoading || cards.length === 0}
          >
            .json
          </button>
          <button
            className="px-2.5 py-1.5 bg-bg-input hover:bg-border-light text-text-secondary rounded-sm text-xxs border border-border-default transition-colors active:scale-95"
            onClick={() => handleExport('csv')}
            disabled={isLoading || cards.length === 0}
          >
            .csv
          </button>
          <button
            className="px-2.5 py-1.5 bg-bg-input hover:bg-border-light text-text-secondary rounded-sm text-xxs border border-border-default transition-colors active:scale-95"
            onClick={() => handleExport('markdown')}
            disabled={isLoading || cards.length === 0}
          >
            .md
          </button>
          <button
            className="px-2.5 py-1.5 bg-bg-input hover:bg-border-light text-text-secondary rounded-sm text-xxs border border-border-default transition-colors active:scale-95"
            onClick={() => handleExport('text')}
            disabled={isLoading || cards.length === 0}
          >
            .txt
          </button>
        </div>
      </div>

      {/* ========== QUICK ACCESS (Single Card) ========== */}
      {singleSelected && selectedCard && (
        <div className="space-y-4 mb-6">
          <h3 className="text-text-muted uppercase font-semibold text-xxs tracking-wider border-b border-border-default pb-2 flex items-center gap-2">
            <Link size={14} className="text-text-dark" /> Quick Access
          </h3>
          <button
            className="w-full bg-bg-input hover:bg-border-light text-accent-indigo-light py-2.5 px-4 rounded-sm mb-4 transition-all text-xs border border-border-default active:scale-95 flex items-center justify-center gap-2"
            onClick={handleOpenInTrello}
            disabled={isLoading}
          >
            🌐 Open in Trello
          </button>
        </div>
      )}

      {/* ========== BATCH OPERATIONS (Multiple Cards) ========== */}
      {hasSelection && numSelected > 1 && (
        <div className="space-y-4 mb-6">
          <h3 className="text-text-muted uppercase font-semibold text-xxs tracking-wider border-b border-border-default pb-2 flex items-center gap-2">
            <Box size={14} className="text-text-dark"/> Batch Operations <span className="text-text-muted font-mono ml-auto">({numSelected})</span>
          </h3>
          <button
            className="w-full bg-bg-input hover:bg-border-light text-text-primary py-2.5 px-4 rounded-sm transition-all text-xs border border-border-default active:scale-95 flex items-center justify-center gap-2"
            onClick={() => toggleMoveCardsModal(true)}
            disabled={isLoading}
          >
            <ListChecks size={14}/> Move Selected...
          </button>
          <button
            className="w-full bg-bg-input hover:bg-border-light text-text-primary py-2.5 px-4 rounded-sm transition-all text-xs border border-border-default active:scale-95 flex items-center justify-center gap-2"
            onClick={() => toggleBulkLabelModal(true)}
            disabled={isLoading}
          >
            <Tag size={14}/> Bulk Add Labels...
          </button>
        </div>
      )}

      {/* ========== CREATE ========== */}
      <div className="space-y-4 mb-6">
        <h3 className="text-text-muted uppercase font-semibold text-xxs tracking-wider border-b border-border-default pb-2 flex items-center gap-2">
          <Plus size={14} className="text-text-dark"/> Create
        </h3>
        <button
          className="w-full bg-status-emerald hover:bg-status-emerald/80 text-white font-semibold py-2.5 px-4 rounded-sm transition-all text-xs active:scale-95 flex items-center justify-center gap-2"
          onClick={handleCreateCard}
          disabled={isLoading || !selectedBoardId}
        >
          <Plus size={14}/> NEW CARD
        </button>
      </div>

      {/* ========== DANGER ZONE ========== */}
      {hasSelection && (
        <div className="space-y-4">
          <h3 className="text-status-red uppercase font-semibold text-xxs tracking-wider border-b border-status-red/50 pb-2 flex items-center gap-2">
            <Trash2 size={14} className="text-status-red"/> Danger Zone
          </h3>
          <button
            className="w-full bg-bg-input hover:bg-status-red/20 text-status-red py-2.5 px-4 rounded-sm transition-all text-xs border border-border-default active:scale-95 flex items-center justify-center gap-2"
            onClick={handleArchiveSelected}
            disabled={isLoading}
          >
            <Archive size={14}/> Archive ({numSelected})
          </button>
          <button
            className="w-full bg-bg-input hover:bg-status-red/20 text-status-red py-2.5 px-4 rounded-sm transition-all text-xs border border-border-default active:scale-95 flex items-center justify-center gap-2"
            onClick={handleDeleteSelected}
            disabled={isLoading}
          >
            <Trash2 size={14}/> Delete Perm. ({numSelected})
          </button>
        </div>
      )}
    </aside>
  );
}
