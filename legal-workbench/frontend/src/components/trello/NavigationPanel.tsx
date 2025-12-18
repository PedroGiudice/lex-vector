import React, { useState } from 'react';
import useTrelloStore, { Board, TrelloList, DueFilter, StatusFilter } from '@/store/trelloStore';
import { ChevronDown, ChevronRight, Search, XCircle, FolderOpen, ListTodo, Tag, Users } from 'lucide-react';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  icon?: React.ElementType; // Optional icon prop
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({ title, children, defaultOpen = true, icon: Icon }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="mb-4 animate-in fade-in slide-in-from-left-2 duration-200">
      <button
        className="flex items-center w-full text-text-muted uppercase font-semibold text-xxs tracking-wider mb-2 hover:text-text-secondary transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        {Icon && <Icon size={12} className="mr-2 text-text-dark" />}
        {isOpen ? <ChevronDown size={14} className="mr-1 text-text-dark" /> : <ChevronRight size={14} className="mr-1 text-text-dark" />}
        {title}
      </button>
      {isOpen && <div className="ml-4 border-l border-border-default pl-2 space-y-1 transition-all duration-150 ease-out">{children}</div>}
    </div>
  );
};

export function NavigationPanel() {
  const {
    boards,
    lists,
    labels,
    members,
    selectedBoardId,
    setSelectedBoardId,
    selectedListId,
    setSelectedListId,
    searchQuery,
    setSearchQuery,
    performSearch,
    isLoading,
    labelFilterIds,
    dueFilter,
    statusFilter,
    memberFilterIds,
    toggleLabelFilter,
    setDueFilter,
    setStatusFilter,
    toggleMemberFilter,
    clearFilters,
  } = useTrelloStore();

  const handleBoardSelect = (boardId: string) => {
    if (boardId !== selectedBoardId) {
      setSelectedBoardId(boardId);
    }
  };

  const handleListSelect = (listId: string) => {
    setSelectedListId(listId === selectedListId ? null : listId); // Toggle selection
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      performSearch(searchQuery);
    } else if (selectedBoardId) {
      useTrelloStore.getState().fetchCardsForBoard(selectedBoardId);
    }
  };

  const handleDueFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDueFilter(e.target.value as DueFilter);
  };

  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setStatusFilter(e.target.value as StatusFilter);
  };

  const cardsInLists = useTrelloStore((state) => state.cards).reduce((acc, card) => {
    acc[card.idList] = (acc[card.idList] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const isFilterActive = labelFilterIds.size > 0 || dueFilter !== 'all' || statusFilter !== 'all' || memberFilterIds.size > 0 || searchQuery.length > 0;

  return (
    <nav className="w-1/5 bg-bg-panel border-r border-border-default flex flex-col p-4 overflow-y-auto text-text-primary text-xs">
      
      {/* Logo/Header Placeholder */}
      <div className="mb-6 px-2">
        <h1 className="text-lg font-bold text-text-primary flex items-center gap-2">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="w-5 h-5 text-accent-indigo">
            <path d="M12 3V5M12 19V21M3 12H5M19 12H21" strokeLinecap="round"/>
            <path d="M5.63604 5.63604L7.05025 7.05025M16.9497 16.9497L18.364 18.364" strokeLinecap="round"/>
            <path d="M5.63604 18.364L7.05025 16.9497M16.9497 7.05025L18.364 5.63604" strokeLinecap="round"/>
            <path d="M12 8L12 16" strokeLinecap="round"/>
          </svg>
          Trello Command
        </h1>
        <p className="text-xxs text-text-muted mt-1">Advanced Board Insights</p>
      </div>

      <CollapsibleSection title="Boards" defaultOpen={true} icon={FolderOpen}>
        <ul className="space-y-1">
          {boards.map((board: Board) => (
            <li
              key={board.id}
              className={`p-1.5 rounded-sm cursor-pointer transition-colors duration-150 ease-in-out font-sans 
              ${selectedBoardId === board.id 
                ? 'bg-accent-indigo/20 text-accent-indigo-light border border-accent-indigo/30'
                : 'hover:bg-bg-input text-text-secondary hover:text-text-primary'}
              `}
              onClick={() => handleBoardSelect(board.id)}
            >
              <span className="ml-1">{board.name}</span>
            </li>
          ))}
        </ul>
      </CollapsibleSection>

      {selectedBoardId && (
        <CollapsibleSection title="Lists" defaultOpen={true} icon={ListTodo}>
          <ul className="space-y-1">
            {lists.map((list: TrelloList) => (
              <li
                key={list.id}
                className={`p-1.5 rounded-sm cursor-pointer transition-colors duration-150 ease-in-out font-sans 
                ${selectedListId === list.id 
                  ? 'bg-accent-indigo/20 text-accent-indigo-light border border-accent-indigo/30'
                  : 'hover:bg-bg-input text-text-secondary hover:text-text-primary'}
                `}
                onClick={() => handleListSelect(list.id)}
              >
                <span className="ml-1">{list.name} <span className="text-text-muted text-xxxs font-mono">({cardsInLists[list.id] || 0})</span></span>
              </li>
            ))}
          </ul>
        </CollapsibleSection>
      )}

      <div className="w-full h-px bg-border-light my-4" />

      <CollapsibleSection title="Quick Filters" defaultOpen={true} icon={Search}> 
        {isFilterActive && (
          <button
            className="flex items-center text-text-muted text-xxs mb-3 hover:text-status-red transition-colors group"
            onClick={clearFilters}
          >
            <XCircle size={14} className="mr-1 text-text-dark group-hover:text-status-red" /> 
            Clear all filters
          </button>
        )}

        {/* Labels Filter */}
        <div className="mb-4">
          <label className="block text-text-muted text-xxs mb-1.5 uppercase tracking-wider flex items-center gap-1">
            <Tag size={10} className="text-text-dark" /> Labels:
          </label>
          <div className="flex flex-col space-y-1 max-h-28 overflow-y-auto pr-2">
            {(labels || []).length > 0 ? (labels || []).map(label => (
              <label key={label.id} className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
                <input
                  type="checkbox"
                  className="form-checkbox text-accent-indigo bg-bg-input border-border-default rounded-sm focus:ring-accent-indigo focus:ring-1"
                  checked={labelFilterIds.has(label.id)}
                  onChange={() => toggleLabelFilter(label.id)}
                />
                <span className="flex items-center"><span className={`w-2.5 h-2.5 rounded-sm inline-block mr-1`} style={{ backgroundColor: label.color }}></span> {label.name}</span>
              </label>
            )) : <span className="text-text-muted text-xxs">No labels available</span>}
          </div>
        </div>

        {/* Due Date Filter */}
        <div className="mb-4">
          <label className="block text-text-muted text-xxs mb-1.5 uppercase tracking-wider flex items-center gap-1">
            <ListTodo size={10} className="text-text-dark" /> Due Date:
          </label>
          <div className="space-y-1">
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="dueDateFilter" value="all" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={dueFilter === 'all'}
                onChange={handleDueFilterChange}
              />
              <span>All</span>
            </label>
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="dueDateFilter" value="today" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={dueFilter === 'today'}
                onChange={handleDueFilterChange}
              />
              <span>Today</span>
            </label>
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="dueDateFilter" value="week" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={dueFilter === 'week'}
                onChange={handleDueFilterChange}
              />
              <span>This Week</span>
            </label>
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="dueDateFilter" value="overdue" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={dueFilter === 'overdue'}
                onChange={handleDueFilterChange}
              />
              <span>Overdue</span>
            </label>
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="dueDateFilter" value="none" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={dueFilter === 'none'}
                onChange={handleDueFilterChange}
              />
              <span>No Due Date</span>
            </label>
          </div>
        </div>

        {/* Status Filter */}
        <div className="mb-4">
          <label className="block text-text-muted text-xxs mb-1.5 uppercase tracking-wider flex items-center gap-1">
            <Tag size={10} className="text-text-dark" /> Status:
          </label>
          <div className="space-y-1">
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="statusFilter" value="all" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={statusFilter === 'all'}
                onChange={handleStatusFilterChange}
              />
              <span>All</span>
            </label>
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="statusFilter" value="open" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={statusFilter === 'open'}
                onChange={handleStatusFilterChange}
              />
              <span>Open</span>
            </label>
            <label className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
              <input type="radio" name="statusFilter" value="archived" className="form-radio text-accent-indigo bg-bg-input border-border-default focus:ring-accent-indigo focus:ring-1"
                checked={statusFilter === 'archived'}
                onChange={handleStatusFilterChange}
              />
              <span>Archived</span>
            </label>
          </div>
        </div>

        {/* Members Filter */}
        <div className="mb-4">
          <label className="block text-text-muted text-xxs mb-1.5 uppercase tracking-wider flex items-center gap-1">
            <Users size={10} className="text-text-dark" /> Members:
          </label>
          <div className="flex flex-col space-y-1 max-h-28 overflow-y-auto pr-2">
            {(members || []).length > 0 ? (members || []).map(member => (
              <label key={member.id} className="flex items-center space-x-2 text-text-secondary text-xxs cursor-pointer hover:text-text-primary transition-colors">
                <input
                  type="checkbox"
                  className="form-checkbox text-accent-indigo bg-bg-input border-border-default rounded-sm focus:ring-accent-indigo focus:ring-1"
                  checked={memberFilterIds.has(member.id)}
                  onChange={() => toggleMemberFilter(member.id)}
                />
                <span>{member.fullName}</span>
              </label>
            )) : <span className="text-text-muted text-xxs">No members available</span>}
          </div>
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="Advanced Search" defaultOpen={true} icon={Search}>
        <form onSubmit={handleSearchSubmit}>
          <input
            type="text"
            placeholder="@me #urgent due:w"
            className="w-full p-2 bg-bg-input border border-border-default rounded-sm focus:outline-none focus:ring-1 focus:ring-accent-indigo text-text-primary text-xs placeholder:text-text-dark transition-colors"
            value={searchQuery}
            onChange={handleSearchChange}
            disabled={isLoading}
          />
          <p className="text-text-muted text-xxs mt-2 leading-tight">
            Operadores: <span className="font-mono">@member #label due:day|week|month has:attachments is:open|archived</span>
          </p>
        </form>
      </CollapsibleSection>
    </nav>
  );
}
