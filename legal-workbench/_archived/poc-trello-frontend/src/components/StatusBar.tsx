import React from 'react';
import useTrelloStore from '../stores/trelloStore';

const StatusBar: React.FC = () => {
  const { cards, selectedBoardId, selectedListId, selectedCardIds } = useTrelloStore();

  const filteredCards = cards.filter(card => {
    const matchesBoard = selectedBoardId ? card.boardId === selectedBoardId : true;
    const matchesList = selectedListId ? card.listId === selectedListId : true;
    return matchesBoard && matchesList;
  });

  const totalCards = filteredCards.length;
  const selectedCount = selectedCardIds.size;

  return (
    <div className="flex items-center justify-between p-2 border-t border-border bg-surface sticky bottom-0 z-10">
      <span className="text-label text-text-secondary">Selected: {selectedCount} | Total: {totalCards}</span>
      <div className="space-x-2">
        <button
          className="bg-surface border border-border text-text-primary text-sm p-1 rounded hover:bg-surface/70 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          disabled={selectedCount === 0}
        >
          Export Selected
        </button>
        <button
          className="bg-surface border border-border text-text-primary text-sm p-1 rounded hover:bg-surface/70 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          disabled={selectedCount === 0}
        >
          Copy JSON
        </button>
      </div>
    </div>
  );
};

export default StatusBar;
