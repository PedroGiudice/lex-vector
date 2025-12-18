import '@testing-library/jest-dom';

// Mock window.getSelection
global.window.getSelection = jest.fn(() => ({
  toString: jest.fn(() => ''),
  removeAllRanges: jest.fn(),
  addRange: jest.fn(),
  getRangeAt: jest.fn(),
  rangeCount: 0,
  isCollapsed: true,
})) as any;
