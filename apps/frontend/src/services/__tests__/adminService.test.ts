/**
 * Unit tests for the typed AdminService.
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
import { adminService } from '../adminService';

const mockedPost = vi.mocked(api.post);
const mockedGet = vi.mocked(api.get);
const mockedPatch = vi.mocked(api.patch);
const mockedDelete = vi.mocked(api.delete);

describe('adminService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getStats', () => {
    it('GETs /admin/stats and returns the envelope', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          total_users: 10,
          total_enrollments: 7,
          total_verifications: 120,
          success_rate: 0.91,
          active_users_24h: 4,
          failed_verifications_24h: 11,
          daily_verifications: [
            { date: '2024-01-01', count: 12 },
            { date: '2024-01-02', count: 8 },
          ],
        },
      });

      const result = await adminService.getStats();

      expect(mockedGet).toHaveBeenCalledWith('/admin/stats');
      expect(result.total_users).toBe(10);
      expect(result.daily_verifications).toHaveLength(2);
    });
  });

  describe('getUsers', () => {
    it('sends page + page_size query params and parses the envelope', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          users: [
            {
              id: 'u-1',
              first_name: 'Ana',
              last_name: 'Pérez',
              email: 'ana@x.com',
              role: 'user',
              is_active: true,
              status: 'active',
              enrollment_status: 'enrolled',
              created_at: '2024-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 2,
          page_size: 25,
          total_pages: 1,
        },
      });

      const result = await adminService.getUsers(2, 25);

      expect(mockedGet).toHaveBeenCalledWith('/admin/users', {
        params: { page: 2, page_size: 25 },
      });
      expect(result.users[0]!.email).toBe('ana@x.com');
      expect(result.total).toBe(1);
    });
  });

  describe('getUserDetails / getUserHistory', () => {
    it('GETs /admin/users/{id}', async () => {
      mockedGet.mockResolvedValueOnce({ data: { id: 'u-1', email: 'x@y.com' } });
      await adminService.getUserDetails('u-1');
      expect(mockedGet).toHaveBeenCalledWith('/admin/users/u-1');
    });

    it('GETs the verification history through /verification/user/{id}/history', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          success: true,
          history: { user_id: 'u-1', total_attempts: 0, recent_attempts: [] },
        },
      });
      await adminService.getUserHistory('u-1');
      expect(mockedGet).toHaveBeenCalledWith('/verification/user/u-1/history');
    });
  });

  describe('getPhraseRules', () => {
    it('GETs /admin/phrase-rules', async () => {
      mockedGet.mockResolvedValueOnce({
        data: [
          {
            id: '1',
            rule_name: 'similarity_threshold',
            rule_type: 'threshold',
            rule_value: 0.8,
            is_active: true,
            description: 'min similarity',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ],
      });
      const result = await adminService.getPhraseRules();
      expect(mockedGet).toHaveBeenCalledWith('/admin/phrase-rules');
      expect(result[0]!.rule_name).toBe('similarity_threshold');
    });
  });

  describe('updateRule', () => {
    it('PATCHes /admin/phrase-rules/{rule} with {new_value}', async () => {
      mockedPatch.mockResolvedValueOnce({
        data: { success: true, rule: { rule_name: 'r', rule_value: 0.9 } as never, message: 'ok' },
      });
      await adminService.updateRule('r', 0.9);
      expect(mockedPatch).toHaveBeenCalledWith('/admin/phrase-rules/r', { new_value: 0.9 });
    });
  });

  describe('toggleRule', () => {
    it('POSTs /admin/phrase-rules/{rule}/toggle', async () => {
      mockedPost.mockResolvedValueOnce({
        data: { success: true, rule: { rule_name: 'r' } as never, message: 'toggled' },
      });
      await adminService.toggleRule('r');
      expect(mockedPost).toHaveBeenCalledWith('/admin/phrase-rules/r/toggle');
    });
  });

  describe('getLogs', () => {
    it('GETs /admin/activity with limit and optional action filters', async () => {
      mockedGet.mockResolvedValueOnce({ data: [] });
      await adminService.getLogs(50, 'login');
      expect(mockedGet).toHaveBeenCalledWith('/admin/activity?limit=50&action=login');
    });

    it('omits the action param when not provided', async () => {
      mockedGet.mockResolvedValueOnce({ data: [] });
      await adminService.getLogs(100);
      expect(mockedGet).toHaveBeenCalledWith('/admin/activity?limit=100');
    });
  });

  describe('deleteUser', () => {
    it('DELETEs /admin/users/{id}', async () => {
      mockedDelete.mockResolvedValueOnce({ data: { message: 'gone' } });
      await adminService.deleteUser('u-1');
      expect(mockedDelete).toHaveBeenCalledWith('/admin/users/u-1');
    });
  });

  describe('updateUser', () => {
    it('PATCHes /admin/users/{id} with the partial payload', async () => {
      mockedPatch.mockResolvedValueOnce({ data: { message: 'updated' } });
      await adminService.updateUser('u-1', {
        first_name: 'Nuevo',
        email: 'new@x.com',
      });
      expect(mockedPatch).toHaveBeenCalledWith('/admin/users/u-1', {
        first_name: 'Nuevo',
        email: 'new@x.com',
      });
    });
  });
});
