import React from 'react';
import useTrelloStore from '../stores/trelloStore';

const Toolbar: React.FC = () => {
  const {
    boards,
    lists,
    selectedBoardId,
    selectedListId,
    setSelectedBoardId,
    setSelectedListId,
    selectAllCards,
    cards // Access all cards to determine "Copy All" functionality
  } = useTrelloStore();

  const handleBoardChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedBoardId(e.target.value === '' ? null : e.target.value);
  };

  const handleListChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedListId(e.target.value === '' ? null : e.target.value);
  };

  const filteredLists = selectedBoardId
    ? lists.filter((list) => list.boardId === selectedBoardId)
    : [];

  return (
    <div className="flex items-center justify-between p-2 border-b border-border bg-surface sticky top-0 z-10">
      <div className="flex space-x-2">
        <select
          className="bg-surface border border-border text-text-primary text-sm p-1 rounded focus:outline-none focus:border-accent"
          value={selectedBoardId || ''}
          onChange={handleBoardChange}
        >
          <option value="">All Boards ▼</option>
          {boards.map((board) => (
            <option key={board.id} value={board.id}>
              {board.name}
            </option>
          ))}
        </select>
        <select
          className="bg-surface border border-border text-text-primary text-sm p-1 rounded focus:outline-none focus:border-accent"
          value={selectedListId || ''}
          onChange={handleListChange}
          disabled={!selectedBoardId} // Disable list selection if no board is selected
        >
          <option value="">All Lists ▼</option>
          {filteredLists.map((list) => (
            <option key={list.id} value={list.id}>
              {list.name}
            </option>
          ))}
        </select>
        <button className="bg-surface border border-border text-text-primary text-sm p-1 rounded hover:bg-surface/70 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent">Filter ▼</button>
      </div>
      <div className="flex space-x-2">
        <button className="bg-surface border border-border text-text-primary text-sm p-1 rounded hover:bg-surface/70 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent">Export ▼</button>
        <button
          className="bg-surface border border-border text-text-primary text-sm p-1 rounded hover:bg-surface/70 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent"
          onClick={selectAllCards}
          disabled={cards.length === 0}
        >
          Copy All
        </button>
      </div>
    </div>
  );
};

export default Toolbar;
