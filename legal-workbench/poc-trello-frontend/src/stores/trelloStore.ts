import { create } from 'zustand';

interface TrelloBoard {
  id: string;
  name: string;
}

interface TrelloList {
  id: string;
  name: string;
  boardId: string;
}

interface TrelloCard {
  id: string;
  name: string;
  desc: string;
  labels: string[];
  due: string | null;
  members: string[];
  listId: string;
  boardId: string;
  // Add other fields as per spec's Card Detail Panel
}

interface TrelloState {
  boards: TrelloBoard[];
  lists: TrelloList[];
  cards: TrelloCard[];
  selectedBoardId: string | null;
  selectedListId: string | null;
  selectedCardIds: Set<string>;
  setBoards: (boards: TrelloBoard[]) => void;
  setLists: (lists: TrelloList[]) => void;
  setCards: (cards: TrelloCard[]) => void;
  setSelectedBoardId: (id: string | null) => void;
  setSelectedListId: (id: string | null) => void;
  toggleCardSelection: (cardId: string) => void;
  clearCardSelection: () => void;
  selectAllCards: () => void;
  // Dummy data initialization
  initializeDummyData: () => void;
}

const useTrelloStore = create<TrelloState>((set, get) => ({
  boards: [],
  lists: [],
  cards: [],
  selectedBoardId: null,
  selectedListId: null,
  selectedCardIds: new Set(),

  setBoards: (boards) => set({ boards }),
  setLists: (lists) => set({ lists }),
  setCards: (cards) => set({ cards }),
  setSelectedBoardId: (id) => set({ selectedBoardId: id, selectedListId: null }),
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
      selectedCardIds: new Set(state.cards.filter(card => {
        const matchesBoard = state.selectedBoardId ? card.boardId === state.selectedBoardId : true;
        const matchesList = state.selectedListId ? card.listId === state.selectedListId : true;
        return matchesBoard && matchesList;
      }).map(card => card.id)),
    })),

  initializeDummyData: () => {
    const dummyBoards: TrelloBoard[] = [
      { id: 'board-1', name: 'Legal Case Management' },
      { id: 'board-2', name: 'Contract Review' },
      { id: 'board-3', name: 'Compliance Audits' },
    ];

    const dummyLists: TrelloList[] = [
      { id: 'list-1-1', name: 'Inbox', boardId: 'board-1' },
      { id: 'list-1-2', name: 'In Progress', boardId: 'board-1' },
      { id: 'list-1-3', name: 'Completed', boardId: 'board-1' },
      { id: 'list-2-1', name: 'Pending Review', boardId: 'board-2' },
      { id: 'list-2-2', name: 'Under Review', boardId: 'board-2' },
      { id: 'list-3-1', name: 'Q1 2024', boardId: 'board-3' },
    ];

    const dummyCards: TrelloCard[] = Array.from({ length: 50 }).map((_, i) => {
      const boardId = i % 3 === 0 ? 'board-1' : (i % 3 === 1 ? 'board-2' : 'board-3');
      const listOptions = dummyLists.filter(list => list.boardId === boardId);
      const listId = listOptions[Math.floor(Math.random() * listOptions.length)].id;

      const labels = i % 5 === 0 ? ['Urgente', 'Contencioso'] : (i % 5 === 1 ? ['Em Andamento'] : ['Documentos', 'Revisão']);
      const members = i % 2 === 0 ? ['PGR', 'LGP'] : ['JAS'];
      const due = i % 4 === 0 ? '2024-12-25' : (i % 4 === 1 ? '2024-12-10' : null);

      return {
        id: `card-${i + 1}`,
        name: `Case #${1000 + i} - Client Name ${String.fromCharCode(65 + i % 26)}`,
        desc: `This is a detailed description for case #${1000 + i}. It involves legal analysis and document review.`,
        labels: labels,
        due: due,
        members: members,
        listId: listId,
        boardId: boardId,
      };
    });

    set({
      boards: dummyBoards,
      lists: dummyLists,
      cards: dummyCards,
      selectedBoardId: dummyBoards[0].id, // Select first board by default
      selectedListId: dummyLists.find(l => l.boardId === dummyBoards[0].id)?.id || null, // Select first list of first board
    });
  },
}));

export default useTrelloStore;
