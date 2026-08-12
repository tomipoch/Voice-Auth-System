import { describe, it, expect, vi, beforeEach } from 'vitest';
import { adminService, challengeService, phraseService } from '../apiServices';
import api from '../api';

// Mock the api module
vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('adminService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getUsers', () => {
    it('successfully retrieves users list', async () => {
      const mockResponse = {
        data: {
          items: [
            { id: '1', email: 'user1@example.com', role: 'user' },
            { id: '2', email: 'user2@example.com', role: 'admin' },
          ],
          total: 2,
          page: 1,
          limit: 10,
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await adminService.getUsers(1, 10);

      expect(api.get).toHaveBeenCalledWith('/admin/users?page=1&limit=10');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getStats', () => {
    it('successfully retrieves system stats', async () => {
      const mockResponse = {
        data: {
          totalUsers: 100,
          totalVerifications: 500,
          successRate: 95,
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await adminService.getStats();

      expect(api.get).toHaveBeenCalledWith('/admin/stats');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('deleteUser', () => {
    it('successfully deletes a user', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: { message: 'User deleted' },
        },
      };

      vi.mocked(api.delete).mockResolvedValue(mockResponse);

      const result = await adminService.deleteUser('user-1');

      expect(api.delete).toHaveBeenCalledWith('/admin/users/user-1');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('updateUser', () => {
    it('successfully updates a user', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: { id: 'user-1', role: 'admin' },
        },
      };

      vi.mocked(api.patch).mockResolvedValue(mockResponse);

      const result = await adminService.updateUser('user-1', { role: 'admin' });

      expect(api.patch).toHaveBeenCalledWith('/admin/users/user-1', { role: 'admin' });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getRecentActivity', () => {
    it('successfully retrieves recent activity', async () => {
      const mockResponse = {
        data: [
          { id: '1', type: 'login', username: 'user1', timestamp: '2024-01-01' },
          { id: '2', type: 'verification', username: 'user2', timestamp: '2024-01-02' },
        ],
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await adminService.getRecentActivity(10);

      expect(api.get).toHaveBeenCalledWith('/admin/activity?limit=10');
      expect(result).toEqual(mockResponse.data);
    });
  });
});

describe('challengeService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getEnrollmentPhrase', () => {
    it('successfully retrieves enrollment phrase', async () => {
      const mockResponse = {
        data: [{ id: 'phrase-1', text: 'Test enrollment phrase', difficulty: 'medium' }],
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await challengeService.getEnrollmentPhrase();

      expect(api.get).toHaveBeenCalledWith('/phrases/random?count=1&difficulty=medium');
      expect(result.phrase).toBe('Test enrollment phrase');
    });
  });

  describe('getVerificationPhrase', () => {
    it('successfully retrieves verification phrase', async () => {
      const mockResponse = {
        data: [{ id: 'phrase-2', text: 'Test verification phrase', difficulty: 'easy' }],
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await challengeService.getVerificationPhrase();

      expect(api.get).toHaveBeenCalledWith('/phrases/random?count=1');
      expect(result.phrase).toBe('Test verification phrase');
    });
  });
});

describe('phraseService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listPhrases', () => {
    it('successfully lists phrases', async () => {
      const mockResponse = {
        data: [
          { id: '1', text: 'Phrase 1', difficulty: 'easy' },
          { id: '2', text: 'Phrase 2', difficulty: 'medium' },
        ],
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await phraseService.listPhrases('medium', 'es', 100);

      expect(api.get).toHaveBeenCalled();
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getStats', () => {
    it('successfully retrieves phrase stats', async () => {
      const mockResponse = {
        data: {
          total: 100,
          easy: 30,
          medium: 40,
          hard: 30,
          language: 'es',
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await phraseService.getStats('es');

      expect(api.get).toHaveBeenCalledWith('/phrases/stats?language=es');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('updateStatus', () => {
    it('successfully updates phrase status', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: { message: 'Status updated' },
        },
      };

      vi.mocked(api.patch).mockResolvedValue(mockResponse);

      const result = await phraseService.updateStatus('phrase-1', true);

      expect(api.patch).toHaveBeenCalledWith('/phrases/phrase-1/status?is_active=true');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('deletePhrase', () => {
    it('successfully deletes a phrase', async () => {
      const mockResponse = {
        data: {
          success: true,
          data: { message: 'Phrase deleted' },
        },
      };

      vi.mocked(api.delete).mockResolvedValue(mockResponse);

      const result = await phraseService.deletePhrase('phrase-1');

      expect(api.delete).toHaveBeenCalledWith('/phrases/phrase-1');
      expect(result).toEqual(mockResponse.data);
    });
  });
});
