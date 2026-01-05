import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.getSelection (required by some components)
Object.defineProperty(window, 'getSelection', {
  writable: true,
  value: vi.fn(() => ({
    toString: vi.fn(() => ''),
    removeAllRanges: vi.fn(),
    addRange: vi.fn(),
    getRangeAt: vi.fn(),
    rangeCount: 0,
    isCollapsed: true,
  })),
});

// Mock URL.createObjectURL and URL.revokeObjectURL for file handling tests
Object.defineProperty(URL, 'createObjectURL', {
  writable: true,
  value: vi.fn(() => 'blob:mock-url'),
});

Object.defineProperty(URL, 'revokeObjectURL', {
  writable: true,
  value: vi.fn(),
});
