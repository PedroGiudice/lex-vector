import React from 'react';
import useTrelloStore, { Card, TrelloList } from '@/store/trelloStore';
import { format } from 'date-fns';
import { Loader2 } from 'lucide-react';

export function DataTable() {
  const {
    cards,
    lists,
    labels,
    members,
    selectedCardIds,
    toggleCardSelection,
    clearCardSelection,
    selectAllCards,
    selectedBoardId,
    selectedListId,
    isLoading,
    error,
    labelFilterIds,
    dueFilter,
    statusFilter,
    memberFilterIds,
  } = useTrelloStore();

  const allCards = useTrelloStore((state) => state.cards);

  const labelMap = new Map((labels || []).map(label => [label.id, label]));
  const memberMap = new Map((members || []).map(member => [member.id, member]));

  const filteredCards = allCards.filter(card => {
    if (selectedListId && card.idList !== selectedListId) {
      return false;
    }

    if (labelFilterIds.size > 0) {
      const cardHasMatchingLabel = (card.idLabels || []).some(labelId => labelFilterIds.has(labelId));
      if (!cardHasMatchingLabel) {
        return false;
      }
    }

    if (dueFilter !== 'all') {
      const now = new Date();
      const cardDueDate = card.due ? new Date(card.due) : null;
      if (!cardDueDate) {
        if (dueFilter !== 'none') {
          return false;
        }
      } else {
        const isOverdue = cardDueDate < now && !card.closed;
        const isToday = cardDueDate.toDateString() === now.toDateString();
        const startOfWeek = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay());
        const endOfWeek = new Date(startOfWeek.getFullYear(), startOfWeek.getMonth(), startOfWeek.getDate() + 7);
        const isThisWeek = cardDueDate >= startOfWeek && cardDueDate < endOfWeek;

        switch (dueFilter) {
          case 'today':
            if (!isToday) return false;
            break;
          case 'week':
            if (!isThisWeek) return false;
            break;
          case 'overdue':
            if (!isOverdue) return false;
            break;
        }
      }
    }

    if (statusFilter !== 'all') {
      if (statusFilter === 'open' && card.closed) return false;
      if (statusFilter === 'archived' && !card.closed) return false;
    }

    if (memberFilterIds.size > 0) {
      const cardHasMatchingMember = (card.idMembers || []).some(memberId => memberFilterIds.has(memberId));
      if (!cardHasMatchingMember) {
        return false;
      }
    }

    return true;
  });

  const totalCards = allCards.length;
  const numSelectedCards = selectedCardIds.size;
  const numFilteredCards = filteredCards.length;

  const getListName = (idList: string) => {
    const list = lists.find(l => l.id === idList);
    return list ? list.name : 'Unknown List';
  };

  const getLabelNameAndColor = (labelId: string) => {
    return labelMap.get(labelId);
  };

  const getMemberFullName = (memberId: string) => {
    return memberMap.get(memberId)?.fullName || 'Unknown Member';
  };

  const isAllSelected = numFilteredCards > 0 && numSelectedCards === numFilteredCards;

  const handleSelectAllClick = () => {
    if (isAllSelected) {
      clearCardSelection();
    } else {
      const filteredCardIds = new Set(filteredCards.map(card => card.id));
      useTrelloStore.setState({ selectedCardIds: filteredCardIds });
    }
  };

  if (isLoading && filteredCards.length === 0) {
    return (
      <main className="flex-1 bg-bg-panel flex flex-col items-center justify-center text-text-muted text-sm border-x border-border-default animate-in fade-in duration-200">
        <Loader2 className="animate-spin rounded-full h-8 w-8 text-accent-indigo mb-2" />
        <span className="text-text-secondary">Loading cards...</span>
      </main>
    );
  }

  if (error && filteredCards.length === 0) {
    return (
      <main className="flex-1 bg-bg-panel flex flex-col items-center justify-center text-status-red text-sm border-x border-border-default animate-in fade-in duration-200">
        Error: {error}
      </main>
    );
  }

  if (filteredCards.length === 0 && !isLoading && !error) {
    return (
      <main className="flex-1 bg-bg-panel flex flex-col items-center justify-center text-text-muted text-sm border-x border-border-default animate-in fade-in duration-200">
        <p>No cards found for the selected board/list or with current filters.</p>
      </main>
    );
  }

  return (
    <main className="flex-1 bg-bg-panel flex flex-col overflow-hidden text-text-primary text-xs border-x border-border-default animate-in fade-in duration-200">
      <div className="flex-1 overflow-y-auto">
        <table className="min-w-full text-left font-sans text-xs">
          <thead>
            <tr className="border-b border-border-default bg-bg-panel-1 sticky top-0 z-10">
              <th className="py-2 px-3 w-8">
                <input
                  type="checkbox"
                  className="form-checkbox bg-bg-input border-border-default rounded-sm text-accent-indigo focus:ring-accent-indigo focus:ring-1 transition-colors"
                  checked={isAllSelected}
                  onChange={handleSelectAllClick}
                />
              </th>
              <th className="py-2 px-3 text-text-muted uppercase font-semibold text-xxs tracking-wider cursor-pointer hover:text-accent-indigo-light transition-colors">CARD ↕</th>
              <th className="py-2 px-3 text-text-muted uppercase font-semibold text-xxs tracking-wider cursor-pointer hover:text-accent-indigo-light transition-colors">LIST ↕</th>
              <th className="py-2 px-3 text-text-muted uppercase font-semibold text-xxs tracking-wider cursor-pointer hover:text-accent-indigo-light transition-colors">DUE ↕</th>
              <th className="py-2 px-3 text-text-muted uppercase font-semibold text-xxs tracking-wider">LABELS</th>
              <th className="py-2 px-3 text-text-muted uppercase font-semibold text-xxs tracking-wider">MEMBERS</th>
            </tr>
          </thead>
          <tbody>
            {filteredCards.map((card: Card) => (
              <tr
                key={card.id}
                className={`border-b border-border-default cursor-pointer transition-colors duration-100 ease-in-out 
                ${selectedCardIds.has(card.id) 
                  ? 'bg-accent-indigo/10' 
                  : 'hover:bg-bg-input'}`}
                onClick={() => toggleCardSelection(card.id)}
              >
                <td className="py-2 px-3">
                  <input
                    type="checkbox"
                    className="form-checkbox bg-bg-input border-border-default rounded-sm text-accent-indigo focus:ring-accent-indigo focus:ring-1 transition-colors"
                    checked={selectedCardIds.has(card.id)}
                    onChange={() => toggleCardSelection(card.id)}
                  />
                </td>
                <td className="py-2 px-3 text-accent-indigo-light font-medium">{card.name}</td>
                <td className="py-2 px-3 text-text-secondary">{getListName(card.idList)}</td>
                <td className={`py-2 px-3 font-mono ${card.due && new Date(card.due) < new Date() && !card.closed ? 'text-status-red' : 'text-text-primary'}`}>
                  {card.due ? format(new Date(card.due), 'dd/MM') : '-'}
                </td>
                <td className="py-2 px-3">
                  {(card.idLabels || []).map((labelId, index) => {
                    const label = getLabelNameAndColor(labelId);
                    return label ? (
                      <span
                        key={index}
                        className={`w-2 h-2 rounded-full inline-block mr-1`}
                        style={{ backgroundColor: label.color || '#cccccc' }} // Fallback color
                        title={label.name}
                      ></span>
                    ) : null;
                  })}
                </td>
                <td className="py-2 px-3">
                  {(card.idMembers || []).length > 0 ? (
                    <div className="flex items-center space-x-1">
                      {(card.idMembers || []).map(memberId => {
                        const memberFullName = getMemberFullName(memberId);
                        const initials = memberFullName.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
                        return (
                          <span 
                            key={memberId} 
                            title={memberFullName}
                            className="text-text-secondary font-mono text-xxxs rounded-full bg-bg-input p-1 flex items-center justify-center w-5 h-5"
                          >
                            {initials}
                          </span>
                        );
                      })}
                    </div>
                  ) : <span className="text-text-dark">-</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Status Bar */}
      <div className="flex justify-between items-center p-3 border-t border-border-default bg-bg-panel-1 text-xxs text-text-muted font-mono shrink-0">
        <span>Selected: <span className="text-text-primary">{numSelectedCards}</span></span>
        <span>Total: <span className="text-text-primary">{totalCards}</span></span>
        <span>Filtered: <span className="text-text-primary">{numFilteredCards}</span></span>
        <span>🔄 Last Sync: <span className="text-text-primary">{useTrelloStore.getState().lastSync ? format(useTrelloStore.getState().lastSync as Date, 'HH:mm:ss') : 'N/A'}</span></span>
      </div>
    </main>
  );
}
