import React from 'react';
import { render, screen } from '@testing-library/react';
import StatusBar from './StatusBar';
import useTrelloStore from '../stores/trelloStore';

// Mock the zustand store
jest.mock('../stores/trelloStore', () => ({
  __esModule: true,
  default: jest.fn(),
}));

describe('StatusBar', () => {
  const mockStore = {
    cards: [],
    selectedBoardId: null,
    selectedListId: null,
    selectedCardIds: new Set<string>(),
  };

  beforeEach(() => {
    (useTrelloStore as jest.Mock).mockReturnValue(mockStore);
  });

  it('renders correctly with 0 selected and 0 total cards initially', () => {
    render(<StatusBar />);
    expect(screen.getByText('Selected: 0 | Total: 0')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Export Selected/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Copy JSON/i })).toBeDisabled();
  });

  it('renders correctly with some selected cards', () => {
    const cards = [
      { id: 'c1', name: 'Card 1', boardId: 'b1', listId: 'l1', labels: [], due: null, members: [], desc: '' },
      { id: 'c2', name: 'Card 2', boardId: 'b1', listId: 'l1', labels: [], due: null, members: [], desc: '' },
      { id: 'c3', name: 'Card 3', boardId: 'b1', listId: 'l1', labels: [], due: null, members: [], desc: '' },
    ];
    const selected = new Set(['c1', 'c3']);

    (useTrelloStore as jest.Mock).mockReturnValue({
      ...mockStore,
      cards: cards,
      selectedCardIds: selected,
    });

    render(<StatusBar />);
    expect(screen.getByText('Selected: 2 | Total: 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Export Selected/i })).toBeEnabled();
    expect(screen.getByRole('button', { name: /Copy JSON/i })).toBeEnabled();
  });

  it('renders correctly when a board and list are selected, affecting total count', () => {
    const cards = [
      { id: 'c1', name: 'Card 1', boardId: 'b1', listId: 'l1', labels: [], due: null, members: [], desc: '' },
      { id: 'c2', name: 'Card 2', boardId: 'b1', listId: 'l1', labels: [], due: null, members: [], desc: '' },
      { id: 'c3', name: 'Card 3', boardId: 'b2', listId: 'l2', labels: [], due: null, members: [], desc: '' },
    ];
    const selected = new Set(['c1']);

    (useTrelloStore as jest.Mock).mockReturnValue({
      ...mockStore,
      cards: cards,
      selectedBoardId: 'b1',
      selectedListId: 'l1',
      selectedCardIds: selected,
    });

    render(<StatusBar />);
    // Only c1 and c2 match board b1 and list l1, so total is 2, selected is 1
    expect(screen.getByText('Selected: 1 | Total: 2')).toBeInTheDocument();
  });
});
