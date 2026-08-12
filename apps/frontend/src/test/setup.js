import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
import userEvent from '@testing-library/user-event';

// Make userEvent globally available
global.userEvent = userEvent;

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage with proper Object.keys support
function createLocalStorageMock() {
  const mockStorage = {
    _data: {},
    getItem(key) {
      return this._data[key] || null;
    },
    setItem(key, value) {
      this._data[key] = value.toString();
      // Add as property for Object.keys() to find it
      this[key] = value.toString();
    },
    removeItem(key) {
      delete this._data[key];
      delete this[key];
    },
    clear() {
      const keys = Object.keys(this._data);
      keys.forEach((key) => {
        delete this._data[key];
        delete this[key];
      });
    },
    get length() {
      return Object.keys(this._data).length;
    },
    key(index) {
      const keys = Object.keys(this._data);
      return keys[index] || null;
    },
  };

  return mockStorage;
}

global.localStorage = createLocalStorageMock();

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return [];
  }
  unobserve() {}
};
