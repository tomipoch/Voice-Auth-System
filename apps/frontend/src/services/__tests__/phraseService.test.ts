/**
 * Unit tests for the typed PhraseService.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { phraseService } from '../phraseService';

const mockedGet = vi.mocked(api.get);
const mockedPatch = vi.mocked(api.patch);
const mockedDelete = vi.mocked(api.delete);

describe('phraseService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getStats', () => {
    it('GETs /phrases/stats?language=... with default es', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          total: 100,
          active: 80,
          inactive: 20,
          easy: 30,
          medium: 40,
          hard: 30,
          language: 'es',
        },
      });
      const result = await phraseService.getStats();
      expect(mockedGet).toHaveBeenCalledWith('/phrases/stats', { params: { language: 'es' } });
      expect(result.total).toBe(100);
    });

    it('passes the language argument through', async () => {
      mockedGet.mockResolvedValueOnce({ data: { total: 0 } });
      await phraseService.getStats('en');
      expect(mockedGet).toHaveBeenCalledWith('/phrases/stats', { params: { language: 'en' } });
    });
  });

  describe('getPhrases', () => {
    it('serializes only provided filters into query params', async () => {
      mockedGet.mockResolvedValueOnce({
        data: { phrases: [], total: 0, page: 1, limit: 50, total_pages: 0 },
      });
      await phraseService.getPhrases({
        page: 1,
        limit: 25,
        difficulty: 'hard',
        is_active: true,
        search: 'hola',
        book_id: 'b-1',
        author: 'Cervantes',
      });
      expect(mockedGet).toHaveBeenCalledWith('/phrases/list', {
        params: {
          page: 1,
          limit: 25,
          difficulty: 'hard',
          is_active: true,
          search: 'hola',
          book_id: 'b-1',
          author: 'Cervantes',
        },
      });
    });

    it('omits is_active when null', async () => {
      mockedGet.mockResolvedValueOnce({
        data: { phrases: [], total: 0, page: 1, limit: 10, total_pages: 0 },
      });
      await phraseService.getPhrases({ page: 1, limit: 10, is_active: null as never });
      const [, opts] = mockedGet.mock.calls[0]!;
      const params = (opts as { params: Record<string, unknown> }).params;
      expect('is_active' in params).toBe(false);
    });
  });

  describe('getRandomPhrases', () => {
    it('GETs /phrases/random with count, difficulty, language', async () => {
      mockedGet.mockResolvedValueOnce({ data: [] });
      await phraseService.getRandomPhrases(3, 'easy', 'es');
      expect(mockedGet).toHaveBeenCalledWith('/phrases/random', {
        params: { count: 3, difficulty: 'easy', language: 'es' },
      });
    });

    it('uses defaults when called with no args', async () => {
      mockedGet.mockResolvedValueOnce({ data: [] });
      await phraseService.getRandomPhrases();
      expect(mockedGet).toHaveBeenCalledWith('/phrases/random', {
        params: { count: 1, difficulty: undefined, language: 'es' },
      });
    });
  });

  describe('togglePhraseStatus', () => {
    it('PATCHes /phrases/{id}/status with is_active', async () => {
      mockedPatch.mockResolvedValueOnce({
        data: { success: true, message: 'updated', phrase_id: 'p-1', is_active: false },
      });
      const result = await phraseService.togglePhraseStatus('p-1', false);
      expect(mockedPatch).toHaveBeenCalledWith('/phrases/p-1/status', { is_active: false });
      expect(result.is_active).toBe(false);
    });
  });

  describe('deletePhrase', () => {
    it('DELETEs /phrases/{id}', async () => {
      mockedDelete.mockResolvedValueOnce({
        data: { success: true, message: 'gone', phrase_id: 'p-1' },
      });
      await phraseService.deletePhrase('p-1');
      expect(mockedDelete).toHaveBeenCalledWith('/phrases/p-1');
    });
  });

  describe('getBooks', () => {
    it('GETs /phrases/books', async () => {
      mockedGet.mockResolvedValueOnce({
        data: [
          { id: 'b-1', title: 'Don Quijote', author: 'Cervantes' },
          { id: 'b-2', title: '1984', author: 'Orwell' },
        ],
      });
      const result = await phraseService.getBooks();
      expect(mockedGet).toHaveBeenCalledWith('/phrases/books');
      expect(result).toHaveLength(2);
      expect(result[0]!.title).toBe('Don Quijote');
    });
  });
});
