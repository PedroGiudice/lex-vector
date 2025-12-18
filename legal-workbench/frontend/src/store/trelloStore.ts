import { create } from 'zustand';
import * as trelloApi from '../services/trelloApi'; // Import all functions from trelloApi

// Re-exporting interfaces for convenience
export type Board = trelloApi.Board;
export type TrelloList = trelloApi.TrelloList;
export type Card = trelloApi.Card;
export type Label = trelloApi.Label;
export type Member = trelloApi.Member;

// Filter types
export type DueFilter = 'all' | 'today' | 'week' | 'overdue' | 'none';
export type StatusFilter = 'open' | 'archived' | 'all';

interface TrelloState {
  // Core Data
  boards: Board[];
  lists: TrelloList[];
  cards: Card[];
  labels: Label[];
  members: Member[];

  // UI State
  selectedBoardId: string | null;
  selectedListId: string | null;
  selectedCardIds: Set<string>;
  isLoading: boolean;
  error: string | null;
  lastSync: Date | null;

  // Modal State
  moveCardsModalOpen: boolean;
  bulkLabelModalOpen: boolean;

  // Filter State
  searchQuery: string;
  labelFilterIds: Set<string>;
  dueFilter: DueFilter;
  statusFilter: StatusFilter;
  memberFilterIds: Set<string>;

  // Actions
  setBoards: (boards: Board[]) => void;
  setLists: (lists: TrelloList[]) => void;
  setCards: (cards: Card[]) => void;
  setLabels: (labels: Label[]) => void;
  setMembers: (members: Member[]) => void;
  setSelectedBoardId: (id: string | null) => void;
  setSelectedListId: (id: string | null) => void;
  toggleCardSelection: (cardId: string) => void;
  clearCardSelection: () => void;
  selectAllCards: () => void;

  // Modal Actions
  toggleMoveCardsModal: (isOpen: boolean) => void;
  toggleBulkLabelModal: (isOpen: boolean) => void;

  // Filter Actions
  setSearchQuery: (query: string) => void;
  toggleLabelFilter: (labelId: string) => void;
  setDueFilter: (filter: DueFilter) => void;
  setStatusFilter: (filter: StatusFilter) => void;
  toggleMemberFilter: (memberId: string) => void;
  clearFilters: () => void;

  // Async actions
  fetchInitialData: () => Promise<void>;
  fetchBoardData: (boardId: string) => Promise<void>;
  fetchCardsForBoard: (boardId: string) => Promise<void>;
  performSearch: (query: string) => Promise<void>;
  createCard: (cardData: Parameters<typeof trelloApi.createCard>[0]) => Promise<void>;
  updateCard: (cardId: string, cardData: Parameters<typeof trelloApi.updateCard>[1]) => Promise<void>;
  archiveCard: (cardId: string) => Promise<void>;
  deleteCard: (cardId: string) => Promise<void>;

  // Batch operations
  moveSelectedCards: (targetListId: string) => Promise<void>;
  bulkAddLabels: (labelIds: string[]) => Promise<void>;
  bulkSetDueDate: (dueDate: Date | null) => Promise<void>;
  bulkAssignMembers: (memberIds: string[]) => Promise<void>;
  archiveSelectedCards: () => Promise<void>;
  deleteSelectedCards: () => Promise<void>;
}

const useTrelloStore = create<TrelloState>((set, get) => ({
  // Core Data
  boards: [],
  lists: [],
  cards: [],
  labels: [],
  members: [],

  // UI State
  selectedBoardId: null,
  selectedListId: null,
  selectedCardIds: new Set(),
  isLoading: false,
  error: null,
  lastSync: null,

  // Modal State
  moveCardsModalOpen: false,
  bulkLabelModalOpen: false,

  // Filter State
  searchQuery: '',
  labelFilterIds: new Set(),
  dueFilter: 'all',
  statusFilter: 'open',
  memberFilterIds: new Set(),

  // Actions
  setBoards: (boards) => set({ boards }),
  setLists: (lists) => set({ lists }),
  setCards: (cards) => set({ cards }),
  setLabels: (labels) => set({ labels }),
  setMembers: (members) => set({ members }),
  setSelectedBoardId: (id) => {
    set({
      selectedBoardId: id,
      selectedListId: null,
      selectedCardIds: new Set(),
      labelFilterIds: new Set(),
      dueFilter: 'all',
      statusFilter: 'open',
      memberFilterIds: new Set(),
    });
    if (id) {
      get().fetchBoardData(id);
    } else {
      set({ lists: [], cards: [], labels: [], members: [] });
    }
  },
  setSelectedListId: (id) => set({ selectedListId: id }),
  toggleCardSelection: (cardId) =>
    set((state) => {
      const newSelection = new Set(state.selectedCardIds);
      if (newSelection.has(cardId)) {
        newSelection.delete(cardId);
      } else {
        newSelection.add(cardId);
      }
      return { selectedCardIds: newSelection };
    }),
  clearCardSelection: () => set({ selectedCardIds: new Set() }),
  selectAllCards: () =>
    set((state) => ({
      selectedCardIds: new Set(state.cards.map((card) => card.id)),
    })),

  // Modal Actions
  toggleMoveCardsModal: (isOpen) => set({ moveCardsModalOpen: isOpen }),
  toggleBulkLabelModal: (isOpen) => set({ bulkLabelModalOpen: isOpen }),

  // Filter Actions
  setSearchQuery: (query) => set({ searchQuery: query }),
  toggleLabelFilter: (labelId) =>
    set((state) => {
      const newFilter = new Set(state.labelFilterIds);
      if (newFilter.has(labelId)) {
        newFilter.delete(labelId);
      } else {
        newFilter.add(labelId);
      }
      return { labelFilterIds: newFilter };
    }),
  setDueFilter: (filter) => set({ dueFilter: filter }),
  setStatusFilter: (filter) => set({ statusFilter: filter }),
  toggleMemberFilter: (memberId) =>
    set((state) => {
      const newFilter = new Set(state.memberFilterIds);
      if (newFilter.has(memberId)) {
        newFilter.delete(memberId);
      } else {
        newFilter.add(memberId);
      }
      return { memberFilterIds: newFilter };
    }),
  clearFilters: () => set({
    labelFilterIds: new Set(),
    dueFilter: 'all',
    statusFilter: 'open',
    memberFilterIds: new Set(),
    searchQuery: '',
  }),

  // Async actions
  fetchInitialData: async () => {
    set({ isLoading: true, error: null });
    try {
      const boards = await trelloApi.fetchBoards();
      set({ boards, lastSync: new Date() });
      if (boards.length > 0) {
        const firstBoardId = boards[0].id;
        set({ selectedBoardId: firstBoardId });
        await get().fetchBoardData(firstBoardId);
      } else {
         set({ isLoading: false });
      }
    } catch (err: any) {
      set({ error: err.message, boards: [], lists: [], cards: [], isLoading: false });
      console.error('Failed to fetch initial Trello data:', err);
    }
  },

  fetchBoardData: async (boardId: string) => {
    set({ isLoading: true, error: null });
    try {
      const structure = await trelloApi.fetchBoardStructure(boardId);
      set({
        lists: structure.lists,
        cards: structure.cards,
        // Labels/members are now included in the mocked backend response
        labels: structure.labels,
        members: structure.members,
        lastSync: new Date(),
      });
    } catch (err: any) {
      set({ error: err.message, lists: [], cards: [], labels: [], members: [] });
      console.error(`Failed to fetch board data for ${boardId}:`, err);
    } finally {
      set({ isLoading: false });
    }
  },

  fetchCardsForBoard: async (boardId: string) => {
    await get().fetchBoardData(boardId);
  },

  performSearch: async (queryText: string) => {
    set({ isLoading: true, error: null });
    try {
      const searchResults = await trelloApi.searchCards(queryText);
      set({ cards: searchResults, lastSync: new Date() });
    } catch (err: any) {
      set({ error: err.message });
      console.error(`Failed to perform search for "${queryText}":`, err);
    } finally {
      set({ isLoading: false });
    }
  },

  createCard: async (cardData) => {
    set({ isLoading: true, error: null });
    try {
      const newCard = await trelloApi.createCard(cardData);
      set((state) => ({ cards: [...state.cards, newCard], lastSync: new Date() }));
    } catch (err: any) {
      set({ error: err.message });
      console.error('Failed to create card:', err);
    } finally {
      set({ isLoading: false });
    }
  },

  updateCard: async (cardId, cardData) => {
    try {
      const updatedCard = await trelloApi.updateCard(cardId, cardData);
      set((state) => ({
        cards: state.cards.map((c) => (c.id === cardId ? updatedCard : c)),
        lastSync: new Date(),
      }));
    } catch (err: any) {
      set({ error: err.message });
      console.error(`Failed to update card ${cardId}:`, err);
    }
  },

  archiveCard: async (cardId) => {
    try {
      await trelloApi.archiveCard(cardId);
      set((state) => ({
        cards: state.cards.filter((c) => c.id !== cardId),
        selectedCardIds: new Set([...state.selectedCardIds].filter(id => id !== cardId)),
        lastSync: new Date(),
      }));
    } catch (err: any) {
      set({ error: err.message });
      console.error(`Failed to archive card ${cardId}:`, err);
    }
  },

  deleteCard: async (cardId) => {
    try {
      await trelloApi.deleteCard(cardId);
      set((state) => ({
        cards: state.cards.filter((c) => c.id !== cardId),
        selectedCardIds: new Set([...state.selectedCardIds].filter(id => id !== cardId)),
        lastSync: new Date(),
      }));
    } catch (err: any) {
      set({ error: err.message });
      console.error(`Failed to delete card ${cardId}:`, err);
    } finally {
      set({ isLoading: false });
    }
  },

  // Batch Operations
  moveSelectedCards: async (targetListId: string) => {
    const { selectedCardIds, updateCard } = get();
    set({ isLoading: true });
    try {
      const promises = [...selectedCardIds].map(cardId =>
        updateCard(cardId, { idList: targetListId })
      );
      await Promise.all(promises);
      set((state) => ({
        cards: state.cards.map(card =>
          selectedCardIds.has(card.id) ? { ...card, idList: targetListId } : card
        ),
        selectedCardIds: new Set(),
        moveCardsModalOpen: false,
      }));
    } catch(err) {
      console.error('Failed to move cards:', err);
    } finally {
      set({ isLoading: false });
    }
  },

  bulkAddLabels: async (labelIds: string[]) => {
    const { selectedCardIds, cards, updateCard } = get();
    set({ isLoading: true });
    try {
      const promises = [...selectedCardIds].map(cardId => {
        const card = cards.find(c => c.id === cardId);
        if (!card) return Promise.resolve();
        const newLabelIds = [...new Set([...card.idLabels, ...labelIds])];
        return updateCard(cardId, { idLabels: newLabelIds });
      });
      await Promise.all(promises);
      if (get().selectedBoardId) await get().fetchBoardData(get().selectedBoardId!);
      set({ selectedCardIds: new Set(), bulkLabelModalOpen: false });
    } finally {
      set({ isLoading: false });
    }
  },

  bulkSetDueDate: async (dueDate: Date | null) => {
    const { selectedCardIds, updateCard } = get();
    set({ isLoading: true });
    try {
      const dueValue = dueDate ? dueDate.toISOString() : null;
      const promises = [...selectedCardIds].map(cardId =>
        updateCard(cardId, { due: dueValue })
      );
      await Promise.all(promises);
      if (get().selectedBoardId) await get().fetchBoardData(get().selectedBoardId!);
      set({ selectedCardIds: new Set() });
    } finally {
      set({ isLoading: false });
    }
  },

  bulkAssignMembers: async (memberIds: string[]) => {
    const { selectedCardIds, cards, updateCard } = get();
    set({ isLoading: true });
    try {
      const promises = [...selectedCardIds].map(cardId => {
        const card = cards.find(c => c.id === cardId);
        if (!card) return Promise.resolve();
        const newMemberIds = [...new Set([...card.idMembers, ...memberIds])];
        return updateCard(cardId, { idMembers: newMemberIds });
      });
      await Promise.all(promises);
      if (get().selectedBoardId) await get().fetchBoardData(get().selectedBoardId!);
      set({ selectedCardIds: new Set() });
    } finally {
      set({ isLoading: false });
    }
  },

  archiveSelectedCards: async () => {
    const { selectedCardIds, archiveCard } = get();
    set({ isLoading: true });
    try {
      const promises = [...selectedCardIds].map(cardId => archiveCard(cardId));
      await Promise.all(promises);
    } finally {
      set({ isLoading: false });
    }
  },

  deleteSelectedCards: async () => {
    const { selectedCardIds, deleteCard } = get();
    set({ isLoading: true });
    try {
      const promises = [...selectedCardIds].map(cardId => deleteCard(cardId));
      await Promise.all(promises);
    } finally {
      set({ isLoading: false });
    }
  },
}));

export default useTrelloStore;
