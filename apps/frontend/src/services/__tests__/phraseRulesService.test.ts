/**
 * Unit tests for the typed PhraseRulesService.
 *
 * Note: this service is the admin-level phrase rules accessor
 * (separate from the adminService.updateRule / toggleRule
 * shortcuts). Both code paths exist in the codebase.
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
import { phraseRulesService } from '../phraseRulesService';

const mockedGet = vi.mocked(api.get);
const mockedPatch = vi.mocked(api.patch);
const mockedPost = vi.mocked(api.post);

describe('phraseRulesService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getRules', () => {
    it('GETs /admin/phrase-rules?include_inactive=false by default', async () => {
      mockedGet.mockResolvedValueOnce({ data: [] });
      await phraseRulesService.getRules();
      expect(mockedGet).toHaveBeenCalledWith('/admin/phrase-rules', {
        params: { include_inactive: false },
      });
    });

    it('forwards includeInactive=true when requested', async () => {
      mockedGet.mockResolvedValueOnce({ data: [] });
      await phraseRulesService.getRules(true);
      expect(mockedGet).toHaveBeenCalledWith('/admin/phrase-rules', {
        params: { include_inactive: true },
      });
    });
  });

  describe('updateRule', () => {
    it('PATCHes /admin/phrase-rules/{rule} with {value} (not new_value)', async () => {
      mockedPatch.mockResolvedValueOnce({
        data: { success: true, message: 'ok', rule_name: 'r', new_value: 0.95 },
      });
      const result = await phraseRulesService.updateRule('r', 0.95);
      expect(mockedPatch).toHaveBeenCalledWith('/admin/phrase-rules/r', { value: 0.95 });
      expect(result.new_value).toBe(0.95);
    });
  });

  describe('toggleRule', () => {
    it('POSTs /admin/phrase-rules/{rule}/toggle with is_active query param', async () => {
      mockedPost.mockResolvedValueOnce({
        data: { success: true, message: 'toggled', rule_name: 'r', is_active: true },
      });
      const result = await phraseRulesService.toggleRule('r', true);
      expect(mockedPost).toHaveBeenCalledWith('/admin/phrase-rules/r/toggle', null, {
        params: { is_active: true },
      });
      expect(result.is_active).toBe(true);
    });
  });
});
