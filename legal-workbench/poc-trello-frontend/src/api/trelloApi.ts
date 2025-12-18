// legal-workbench/poc-trello-frontend/src/api/trelloApi.ts

// Define interfaces for API response types
export interface Board {
  id: string;
  name: string;
}

export interface List {
  id: string;
  name: string;
  idBoard: string;
}

export interface Card {
  id: string;
  name: string;
  desc: string;
  idLabels: string[]; // Trello uses idLabels, but our store uses string[]
  due: string | null;
  idMembers: string[];
  idList: string;
  idBoard: string;
  // ... other Trello card fields
}

// Mock API responses
const mockBoards: Board[] = [
  { id: 'trello-board-1', name: 'Trello Board Alpha' },
  { id: 'trello-board-2', name: 'Trello Board Beta' },
];

const mockLists: List[] = [
  { id: 'trello-list-1-1', name: 'To Do', idBoard: 'trello-board-1' },
  { id: 'trello-list-1-2', name: 'Doing', idBoard: 'trello-board-1' },
  { id: 'trello-list-2-1', name: 'Ideas', idBoard: 'trello-board-2' },
];

const mockCards: Card[] = Array.from({ length: 10 }).map((_, i) => ({
  id: `trello-card-${i + 1}`,
  name: `Mock Trello Card ${i + 1}`,
  desc: `Description for mock card ${i + 1}. This would come from Trello.`,
  idLabels: i % 2 === 0 ? ['label-urgent'] : ['label-review'],
  due: i % 3 === 0 ? '2025-01-15T12:00:00.000Z' : null,
  idMembers: i % 2 === 0 ? ['member-alice'] : ['member-bob'],
  idList: i % 2 === 0 ? 'trello-list-1-1' : 'trello-list-1-2',
  idBoard: i % 2 === 0 ? 'trello-board-1' : 'trello-board-2',
}));

// Simulate API calls with delays
const API_BASE_URL = 'http://localhost:8004/api/v1';

export const fetchBoards = async (): Promise<Board[]> => {
  console.log(`[API] Fetching boards from ${API_BASE_URL}/boards`);
  return new Promise((resolve) => {
    setTimeout(() => resolve(mockBoards), 500);
  });
};

export const fetchBoardById = async (boardId: string): Promise<Board | null> => {
  console.log(`[API] Fetching board ${boardId} from ${API_BASE_URL}/boards/${boardId}`);
  return new Promise((resolve) => {
    setTimeout(() => resolve(mockBoards.find(b => b.id === boardId) || null), 300);
  });
};

export const searchCards = async (query: { boardId?: string; listId?: string; searchText?: string }): Promise<Card[]> => {
  console.log(`[API] Searching cards with query:`, query);
  return new Promise((resolve) => {
    setTimeout(() => {
      const results = mockCards.filter(card => {
        const matchesBoard = query.boardId ? card.idBoard === query.boardId : true;
        const matchesList = query.listId ? card.idList === query.listId : true;
        const matchesText = query.searchText
          ? card.name.toLowerCase().includes(query.searchText.toLowerCase()) ||
            card.desc.toLowerCase().includes(query.searchText.toLowerCase())
          : true;
        return matchesBoard && matchesList && matchesText;
      });
      resolve(results);
    }, 700);
  });
};

export const batchFetchCards = async (cardIds: string[]): Promise<Card[]> => {
  console.log(`[API] Batch fetching cards:`, cardIds);
  return new Promise((resolve) => {
    setTimeout(() => {
      const results = mockCards.filter(card => cardIds.includes(card.id));
      resolve(results);
    }, 1000);
  });
};

// Placeholder for export functionality (client-side simulation for POC)
export const exportData = async (data: any[], format: 'json' | 'csv' | 'markdown' | 'text', filename: string) => {
  console.log(`[Export] Exporting ${data.length} items as ${format} to ${filename}`);
  // In a real application, this would trigger a download or send data to backend for server-side export.
  // For POC, we just log.
  switch (format) {
    case 'json':
      console.log('JSON Data:', JSON.stringify(data, null, 2));
      break;
    case 'csv':
      console.log('CSV Data:', data.map(item => Object.values(item).join(',')).join('\n'));
      break;
    case 'markdown':
      console.log('Markdown Data: (implementation needed)');
      break;
    case 'text':
      console.log('Plain Text Data: (implementation needed)');
      break;
  }
  alert(`Exported ${data.length} items as ${format} (check console for details).`);
};
