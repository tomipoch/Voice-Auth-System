import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getSystemTheme, getInitialTheme, applyTheme } from '../theme';

// Mock matchMedia
const createMatchMediaMock = (matches: boolean) => {
  return vi.fn().mockImplementation((query) => ({
    matches,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
};

describe('theme utilities', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear();
    // Reset document classes
    document.documentElement.className = '';
  });

  describe('getSystemTheme', () => {
    it('returns dark when system prefers dark', () => {
      window.matchMedia = createMatchMediaMock(true);
      expect(getSystemTheme()).toBe('dark');
    });

    it('returns light when system prefers light', () => {
      window.matchMedia = createMatchMediaMock(false);
      expect(getSystemTheme()).toBe('light');
    });
  });

  describe('getInitialTheme', () => {
    it('returns stored theme from localStorage', () => {
      localStorage.setItem('voiceauth_local_theme', JSON.stringify('light'));
      expect(getInitialTheme()).toBe('light');
    });

    it('returns light as default when no stored theme', () => {
      window.matchMedia = createMatchMediaMock(false);
      expect(getInitialTheme()).toBe('light'); // Default is light
    });

    it('returns system theme when stored as auto', () => {
      localStorage.setItem('voiceauth_local_theme', JSON.stringify('auto'));
      window.matchMedia = createMatchMediaMock(true);
      expect(getInitialTheme()).toBe('dark');
    });

    it('handles invalid JSON in localStorage', () => {
      localStorage.setItem('voiceauth_local_theme', 'invalid-json');
      window.matchMedia = createMatchMediaMock(false);
      expect(getInitialTheme()).toBe('light'); // Returns light on error
    });
  });

  describe('applyTheme', () => {
    it('adds dark class for dark theme', () => {
      applyTheme('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('removes dark class for light theme', () => {
      document.documentElement.classList.add('dark');
      applyTheme('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });

    it('toggles from light to dark', () => {
      applyTheme('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);

      applyTheme('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);
    });

    it('toggles from dark to light', () => {
      applyTheme('dark');
      expect(document.documentElement.classList.contains('dark')).toBe(true);

      applyTheme('light');
      expect(document.documentElement.classList.contains('dark')).toBe(false);
    });
  });
});
