import React from 'react';
import useTrelloStore from '../stores/trelloStore';

interface TrelloCard {
  id: string;
  name: string;
  desc: string;
  labels: string[];
  due: string | null;
  members: string[];
  listId: string;
  boardId: string;
}

// Helper for date formatting
const formatDate = (dateString: string | null): { text: string; colorClass: string } => {
  if (!dateString) {
    return { text: '-', colorClass: 'text-text-secondary' };
  }

  const today = new Date();
  const dueDate = new Date(dateString);
  const diffTime = dueDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  let text = '';
  let colorClass = 'text-text-secondary'; // Default color

  if (diffDays < 0) {
    text = `Overdue`; // Simpler text for table view
    colorClass = 'text-red-500'; // Overdue color (red from spec)
  } else if (diffDays === 0) {
    text = 'Today';
    colorClass = 'text-warning'; // Due soon (orange from spec)
  } else if (diffDays === 1) {
    text = 'Tomorrow';
    colorClass = 'text-warning';
  } else if (diffDays <= 7) {
    text = `In ${diffDays} days`;
    colorClass = 'text-warning';
  } else {
    text = dueDate.toLocaleDateString('en-GB'); // "DD/MM/YYYY"
  }

  return { text, colorClass };
};


const DataTable: React.FC = () => {
  const {
    cards,
    selectedCardIds,
    toggleCardSelection,
    selectedBoardId,
    selectedListId,
    clearCardSelection,
  } = useTrelloStore();

  // Filter cards based on selected board and list
  const filteredCards = cards.filter(card => {
    const matchesBoard = selectedBoardId ? card.boardId === selectedBoardId : true;
    const matchesList = selectedListId ? card.listId === selectedListId : true;
    return matchesBoard && matchesList;
  });

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      filteredCards.forEach(card => toggleCardSelection(card.id));
    } else {
      clearCardSelection();
    }
  };

  const isAllSelected = filteredCards.length > 0 && filteredCards.every(card => selectedCardIds.has(card.id));

  return (
    <div className="flex-grow overflow-auto">
      <div className="min-w-full inline-block align-middle">
        <div className="overflow-hidden border border-border rounded"> {/* Added border to the table container */}
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-surface sticky top-0">
              <tr>
                <th scope="col" className="px-2 py-1 text-left text-label text-text-secondary uppercase tracking-wider border-r border-border w-10">
                  <input
                    type="checkbox"
                    className="form-checkbox h-3 w-3 text-accent rounded bg-surface border-border focus:ring-accent"
                    onChange={handleSelectAll}
                    checked={isAllSelected}
                    disabled={filteredCards.length === 0}
                  />
                </th>
                <th scope="col" className="px-2 py-1 text-left text-label text-text-secondary uppercase tracking-wider border-r border-border">
                  Card Name
                </th>
                <th scope="col" className="px-2 py-1 text-left text-label text-text-secondary uppercase tracking-wider border-r border-border">
                  Labels
                </th>
                <th scope="col" className="px-2 py-1 text-left text-label text-text-secondary uppercase tracking-wider border-r border-border">
                  Due
                </th>
                <th scope="col" className="px-2 py-1 text-left text-label text-text-secondary uppercase tracking-wider">
                  Members
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredCards.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-2 py-4 text-center text-text-secondary">No cards found for the current selection.</td>
                </tr>
              ) : (
                filteredCards.map((card) => {
                  const isSelected = selectedCardIds.has(card.id);
                  const { text: dueDateText, colorClass: dueDateColorClass } = formatDate(card.due);

                  return (
                    <tr
                      key={card.id}
                      className={`${isSelected ? 'bg-data-highlight/40' : 'hover:bg-data-highlight/20'} even:bg-surface/50 odd:bg-surface`}
                    >
                      <td className="px-2 py-1 whitespace-nowrap border-r border-border text-center w-10">
                        <input
                          type="checkbox"
                          className="form-checkbox h-3 w-3 text-accent rounded bg-surface border-border focus:ring-accent"
                          checked={isSelected}
                          onChange={() => toggleCardSelection(card.id)}
                        />
                      </td>
                      <td className="px-2 py-1 text-data text-text-primary border-r border-border max-w-xs truncate" title={card.name}>
                        {card.name}
                      </td>
                      <td className="px-2 py-1 text-data text-text-secondary border-r border-border">
                        {card.labels.map((label, index) => (
                          <span key={index} className="inline-flex items-center px-1 py-0.5 rounded text-label font-medium bg-accent/20 text-accent mr-1">
                            {label}
                          </span>
                        ))}
                      </td>
                      <td className={`px-2 py-1 whitespace-nowrap text-data ${dueDateColorClass} border-r border-border`}>
                        {dueDateText}
                      </td>
                      <td className="px-2 py-1 whitespace-nowrap text-data text-text-secondary">
                        {card.members.join(', ')}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default DataTable;
