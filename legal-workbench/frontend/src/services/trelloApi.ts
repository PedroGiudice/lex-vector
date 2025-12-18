// legal-workbench/frontend/src/services/trelloApi.ts

// Define interfaces for API response types
export interface Board {
  id: string;
  name: string;
  // Potentially add other board-specific fields like 'desc', 'closed', 'prefs'
}

export interface TrelloList { // Renamed to TrelloList to avoid conflict with JS List
  id: string;
  name: string;
  idBoard: string;
  pos: number; // Position on the board
  closed: boolean;
}

export interface Label {
  id: string;
  idBoard: string;
  name: string;
  color: string; // e.g., 'red', 'green', 'blue'
}

export interface Member {
  id: string;
  fullName: string;
  username: string;
  avatarHash?: string;
}

export interface ChecklistItem {
  id: string;
  name: string;
  state: 'complete' | 'incomplete';
}

export interface Checklist {
  id: string;
  idBoard: string;
  idCard: string;
  name: string;
  checkItems: ChecklistItem[];
}

export interface CustomFieldItem {
  id: string; // Custom field definition ID
  idValue: string; // The specific value ID
  value: any; // The actual value, type depends on custom field type
}

export interface Attachment {
  id: string;
  name: string;
  url: string;
  bytes: number;
  // Add more properties if needed, e.g., mimeType, previews
}

export interface Card {
  id: string;
  name: string;
  desc: string;
  idLabels: string[]; // Array of label IDs
  due: string | null; // ISO 8601 date string
  idMembers: string[]; // Array of member IDs
  idList: string;
  idBoard: string;
  pos: number; // Position in list
  closed: boolean; // True if archived
  shortUrl: string; // Short URL to the card in Trello
  checklists: Checklist[]; // Nested checklists
  customFieldItems?: CustomFieldItem[]; // Nested custom field values
  attachments?: Attachment[]; // Nested attachments
  // Add other relevant Trello card fields as needed
}

const API_BASE_URL = 'http://localhost/api/trello/api/v1';

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      // Add any necessary authentication headers here if applicable
      // 'Authorization': `Bearer YOUR_TOKEN`,
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || `API error: ${response.statusText}`);
  }

  return response.json();
}

export const fetchBoards = async (): Promise<Board[]> => {
  console.log(`[API] Fetching boards from ${API_BASE_URL}/boards`);
  return fetchApi<Board[]>('/boards');
};

// Board Structure Response from backend - UPDATED
export interface BoardStructureResponse {
  board: {
    id: string;
    name: string;
    desc: string;
    closed: boolean;
    url: string;
  };
  lists: TrelloList[];
  cards: Card[];
  // !!! MOCKED DATA: These fields are not returned by the current backend
  //     and are temporarily mocked on the frontend for development purposes.
  //     Backend integration is required to fetch real labels and members.
  labels: Label[];
  members: Member[];
}

export const fetchBoardById = async (boardId: string): Promise<Board> => {
  console.log(`[API] Fetching board ${boardId} from ${API_BASE_URL}/boards/${boardId}`);
  const structure = await fetchApi<BoardStructureResponse>(`/boards/${boardId}`);
  return structure.board;
};

// Fetch complete board structure (board + lists + cards) in one call - MODIFIED
export const fetchBoardStructure = async (boardId: string): Promise<BoardStructureResponse> => {
  console.log(`[API] Fetching board structure for ${boardId} from ${API_BASE_URL}/boards/${boardId}`);
  const rawStructure = await fetchApi<Omit<BoardStructureResponse, 'labels' | 'members'>>(`/boards/${boardId}`);

  // --- MOCK DATA INJECTION START ---
  // This section mocks labels and members that are not provided by the current backend endpoint.
  // This is a temporary frontend workaround.
  const mockLabels: Label[] = [];
  const mockMembers: Member[] = [];

  const uniqueLabelIds = new Set<string>();
  const uniqueMemberIds = new Set<string>();

  // Add null checks for rawStructure.cards and card properties
  if (rawStructure.cards) {
    rawStructure.cards.forEach(card => {
      (card.idLabels || []).forEach(labelId => uniqueLabelIds.add(labelId));
      (card.idMembers || []).forEach(memberId => uniqueMemberIds.add(memberId));
    });
  }

  const labelColors = ['blue', 'green', 'orange', 'red', 'purple', 'yellow', 'sky', 'lime', 'pink', 'black'];
  let colorIndex = 0;

  uniqueLabelIds.forEach(id => {
    mockLabels.push({
      id: id,
      idBoard: boardId, // Associate with the current board
      name: `Label ${id.substring(0, 4)}`, // Generate a simple name
      color: labelColors[colorIndex % labelColors.length],
    });
    colorIndex++;
  });

  uniqueMemberIds.forEach(id => {
    mockMembers.push({
      id: id,
      fullName: `Member ${id.substring(0, 4)}`, // Generate a simple full name
      username: `member-${id.substring(0, 4).toLowerCase()}`,
      avatarHash: undefined, // No avatar hash for mock data
    });
  });

  const structure: BoardStructureResponse = {
    ...rawStructure,
    labels: mockLabels,
    members: mockMembers,
  };
  // --- MOCK DATA INJECTION END ---

  console.log(`[API] MOCKED Labels for board ${boardId}:`, structure.labels);
  console.log(`[API] MOCKED Members for board ${boardId}:`, structure.members);

  return structure;
};

export const fetchLists = async (boardId: string): Promise<TrelloList[]> => {
  console.log(`[API] Fetching lists for board ${boardId} via board structure`);
  const structure = await fetchBoardStructure(boardId);
  return structure.lists;
};

export const fetchCards = async (boardId: string, params?: { customFields?: boolean; checklists?: 'all' }): Promise<Card[]> => {
  console.log(`[API] Fetching cards for board ${boardId} via board structure`);
  const structure = await fetchBoardStructure(boardId);
  return structure.cards;
};

export const searchCards = async (queryText: string): Promise<Card[]> => {
  // Assuming the backend has a /search endpoint that mimics Trello's search.
  // The actual Trello API search is more complex, but for this task,
  // we'll use a simpler mapping as described in "API Mapping".
  console.log(`[API] Searching cards with query: ${queryText}`);
  return fetchApi<Card[]>(`/search?query=${encodeURIComponent(queryText)}&modelTypes=cards`);
};

export const createCard = async (cardData: { idList: string; name: string; desc?: string; pos?: string | number; due?: string | null; idMembers?: string[]; idLabels?: string[]; }): Promise<Card> => {
  console.log(`[API] Creating card in list ${cardData.idList}`);
  return fetchApi<Card>('/cards', {
    method: 'POST',
    body: JSON.stringify(cardData),
  });
};

export const updateCard = async (cardId: string, cardData: Partial<Card>): Promise<Card> => {
  console.log(`[API] Updating card ${cardId}`);
  return fetchApi<Card>(`/cards/${cardId}`, {
    method: 'PUT',
    body: JSON.stringify(cardData),
  });
};

export const moveCard = async (cardId: string, idList: string, pos?: number): Promise<Card> => {
  console.log(`[API] Moving card ${cardId} to list ${idList}`);
  return updateCard(cardId, { idList, pos });
};

export const archiveCard = async (cardId: string): Promise<Card> => {
  console.log(`[API] Archiving card ${cardId}`);
  return updateCard(cardId, { closed: true });
};

export const deleteCard = async (cardId: string): Promise<{ message: string }> => { // Trello API returns success message or empty object
  console.log(`[API] Deleting card ${cardId}`);
  return fetchApi<{ message: string }>(`/cards/${cardId}`, {
    method: 'DELETE',
  });
};

export const addComment = async (cardId: string, text: string): Promise<any> => { // Trello comment object can be large
  console.log(`[API] Adding comment to card ${cardId}`);
  return fetchApi<any>(`/cards/${cardId}/actions/comments`, {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
};

export const addAttachment = async (cardId: string, file: File): Promise<Attachment> => {
  console.log(`[API] Adding attachment to card ${cardId}: ${file.name}`);
  const formData = new FormData();
  formData.append('file', file);
  // Trello API expects a 'file' field for binary uploads
  return fetchApi<Attachment>(`/cards/${cardId}/attachments`, {
    method: 'POST',
    body: formData, // No 'Content-Type': 'application/json' for FormData
  });
};

export const updateChecklistItem = async (cardId: string, checklistId: string, checkItemId: string, state: 'complete' | 'incomplete'): Promise<any> => {
  console.log(`[API] Updating checklist item ${checkItemId} in card ${cardId} to ${state}`);
  // Trello API endpoint is /cards/{idCard}/checklist/{idChecklist}/checkItem/{idCheckItem}
  // This requires a bit more detail than what was specified. Assuming a simpler mapping for now.
  // The actual PUT body for Trello API usually has { state: 'complete' } or { state: 'incomplete' }
  return fetchApi<any>(`/cards/${cardId}/checkItem/${checkItemId}`, { // Simplified path for this task
    method: 'PUT',
    body: JSON.stringify({ state }),
  });
};

export const setCustomField = async (cardId: string, fieldId: string, value: any): Promise<CustomFieldItem> => {
  console.log(`[API] Setting custom field ${fieldId} for card ${cardId} with value:`, value);
  // Trello API expects the value wrapped in a 'value' object: { value: { text: "..." } } or { value: { number: 123 } }
  // The backend mapping needs to handle this, so sending 'value' directly from frontend.
  return fetchApi<CustomFieldItem>(`/cards/${cardId}/customField/${fieldId}/item`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  });
};

// =============================================================================
// DATA EXPORT - Real implementation with file download
// =============================================================================

export interface EnrichedCard extends Card {
  listName?: string;
  labelNames?: { name: string; color: string }[];
  memberNames?: { fullName: string; username: string }[];
}

/**
 * Enrich cards with resolved labels and members (instead of just IDs)
 */
export const enrichCardsForExport = (
  cards: Card[],
  lists: TrelloList[],
  labels: Label[],
  members: Member[]
): EnrichedCard[] => {
  const listMap = new Map(lists.map(l => [l.id, l.name]));
  const labelMap = new Map(labels.map(l => [l.id, { name: l.name, color: l.color }]));
  const memberMap = new Map(members.map(m => [m.id, { fullName: m.fullName, username: m.username }]));

  return cards.map(card => ({
    ...card,
    listName: listMap.get(card.idList) || 'Unknown List',
    labelNames: card.idLabels
      .map(id => labelMap.get(id))
      .filter((l): l is { name: string; color: string } => l !== undefined),
    memberNames: card.idMembers
      .map(id => memberMap.get(id))
      .filter((m): m is { fullName: string; username: string } => m !== undefined),
  }));
};

/**
 * Generate CSV content from cards
 */
const generateCSV = (cards: EnrichedCard[]): string => {
  const headers = ['ID', 'Name', 'Description', 'List', 'Labels', 'Members', 'Due Date', 'Status', 'URL'];
  const rows = cards.map(card => [
    card.id,
    `"${(card.name || '').replace(/"/g, '""')}"`,
    `"${(card.desc || '').replace(/"/g, '""').substring(0, 500)}"`,
    `"${card.listName || ''}"`,
    `"${(card.labelNames || []).map(l => l.name).join(', ')}"`,
    `"${(card.memberNames || []).map(m => m.fullName).join(', ')}"`,
    card.due ? new Date(card.due).toLocaleDateString('pt-BR') : '',
    card.closed ? 'Archived' : 'Open',
    card.shortUrl || '',
  ]);
  return [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
};

/**
 * Generate Markdown content from cards
 */
const generateMarkdown = (cards: EnrichedCard[]): string => {
  const lines: string[] = [
    `# Trello Export - ${new Date().toLocaleDateString('pt-BR')}`,
    ``,
    `**Total Cards:** ${cards.length}`,
    ``,
    `---`,
    ``,
  ];

  cards.forEach((card, index) => {
    lines.push(`## ${index + 1}. ${card.name}`);
    lines.push(``);
    lines.push(`- **List:** ${card.listName || 'N/A'}`);
    lines.push(`- **Status:** ${card.closed ? '🗄️ Archived' : '✅ Open'}`);
    if (card.due) {
      const dueDate = new Date(card.due);
      const isOverdue = dueDate < new Date() && !card.closed;
      lines.push(`- **Due:** ${dueDate.toLocaleDateString('pt-BR')}${isOverdue ? ' ⚠️ OVERDUE' : ''}`);
    }
    if (card.labelNames && card.labelNames.length > 0) {
      lines.push(`- **Labels:** ${card.labelNames.map(l => '`' + l.name + '`').join(', ')}`);
    }
    if (card.memberNames && card.memberNames.length > 0) {
      lines.push(`- **Members:** ${card.memberNames.map(m => m.fullName).join(', ')}`);
    }
    if (card.desc) {
      lines.push(``);
      lines.push(`**Description:**`);
      lines.push(`> ${card.desc.substring(0, 500).replace(/\n/g, '\n> ')}`);
    }
    lines.push(``);
    lines.push(`[Open in Trello](${card.shortUrl})`);
    lines.push(``);
    lines.push(`---`);
    lines.push(``);
  });

  return lines.join('\n');
};

/**
 * Generate plain text content from cards
 */
const generateText = (cards: EnrichedCard[]): string => {
  const lines: string[] = [
    `TRELLO EXPORT - ${new Date().toLocaleDateString('pt-BR')}`,
    `Total Cards: ${cards.length}`,
    `${'='.repeat(60)}`,
    ``,
  ];

  cards.forEach((card, index) => {
    lines.push(`[${index + 1}] ${card.name}`);
    lines.push(`    List: ${card.listName || 'N/A'}`);
    lines.push(`    Status: ${card.closed ? 'Archived' : 'Open'}`);
    if (card.due) {
      lines.push(`    Due: ${new Date(card.due).toLocaleDateString('pt-BR')}`);
    }
    if (card.labelNames && card.labelNames.length > 0) {
      lines.push(`    Labels: ${card.labelNames.map(l => l.name).join(', ')}`);
    }
    if (card.memberNames && card.memberNames.length > 0) {
      lines.push(`    Members: ${card.memberNames.map(m => m.fullName).join(', ')}`);
    }
    if (card.desc) {
      lines.push(`    Description: ${card.desc.substring(0, 200).replace(/\n/g, ' ')}...`);
    }
    lines.push(`    URL: ${card.shortUrl}`);
    lines.push(`${'-'.repeat(60)}`);
  });

  return lines.join('\n');
};

/**
 * Trigger file download in browser
 */
const downloadFile = (content: string, filename: string, mimeType: string) => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

/**
 * Export cards to file - REAL implementation with download
 *
 * @param cards - Cards to export (can be 1 or many)
 * @param format - Export format
 * @param filename - Output filename (without extension)
 * @param lists - Lists for enrichment
 * @param labels - Labels for enrichment
 * @param members - Members for enrichment
 */
export const exportData = async (
  cards: Card[],
  format: 'json' | 'csv' | 'markdown' | 'text',
  filename: string,
  lists: TrelloList[] = [],
  labels: Label[] = [],
  members: Member[] = []
) => {
  console.log(`[Export] Exporting ${cards.length} card(s) as ${format}`);

  // Enrich cards with resolved labels/members
  const enrichedCards = enrichCardsForExport(cards, lists, labels, members);

  let content: string;
  let mimeType: string;
  let extension: string;

  switch (format) {
    case 'json':
      content = JSON.stringify(enrichedCards, null, 2);
      mimeType = 'application/json';
      extension = 'json';
      break;
    case 'csv':
      content = generateCSV(enrichedCards);
      mimeType = 'text/csv;charset=utf-8';
      extension = 'csv';
      break;
    case 'markdown':
      content = generateMarkdown(enrichedCards);
      mimeType = 'text/markdown';
      extension = 'md';
      break;
    case 'text':
      content = generateText(enrichedCards);
      mimeType = 'text/plain';
      extension = 'txt';
      break;
    default:
      throw new Error(`Unknown export format: ${format}`);
  }

  const finalFilename = `${filename}.${extension}`;
  downloadFile(content, finalFilename, mimeType);
  console.log(`[Export] Downloaded: ${finalFilename} (${content.length} bytes)`);
};

/**
 * Copy cards data to clipboard
 */
export const copyToClipboard = async (
  cards: Card[],
  format: 'json' | 'csv' | 'markdown' | 'text',
  lists: TrelloList[] = [],
  labels: Label[] = [],
  members: Member[] = []
): Promise<void> => {
  const enrichedCards = enrichCardsForExport(cards, lists, labels, members);

  let content: string;
  switch (format) {
    case 'json':
      content = JSON.stringify(enrichedCards, null, 2);
      break;
    case 'csv':
      content = generateCSV(enrichedCards);
      break;
    case 'markdown':
      content = generateMarkdown(enrichedCards);
      break;
    case 'text':
      content = generateText(enrichedCards);
      break;
    default:
      content = JSON.stringify(enrichedCards, null, 2);
  }

  await navigator.clipboard.writeText(content);
  console.log(`[Export] Copied ${cards.length} card(s) to clipboard as ${format}`);
};
