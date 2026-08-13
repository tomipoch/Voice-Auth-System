/**
 * Unit tests for the typed VerificationService.
 *
 * Replaces the deleted enrollmentVerificationService.test.ts
 * fragment (see commit I, fase 5) and covers the new typed
 * surface. The flow that previously tested old getVerificationHistory
 * moved to this file with the corrected backend envelope.
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

vi.mock('../../utils/deviceInfo', () => ({
  getDeviceInfo: () => 'mock-device-info',
  getUserAgent: () => 'mock-user-agent',
}));

import api from '../api';
import { verificationService } from '../verificationService';

const mockedPost = vi.mocked(api.post);
const mockedGet = vi.mocked(api.get);

describe('verificationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startVerification', () => {
    it('POSTs JSON to /verification/start', async () => {
      mockedPost.mockResolvedValueOnce({
        data: {
          success: true,
          verification_id: 'v-1',
          user_id: 'u-1',
          challenge_id: 'c-1',
          phrase: 'say this',
          phrase_id: 'p-1',
          expires_at: '2024-01-01T00:00:00Z',
          message: 'ok',
        },
      });

      const result = await verificationService.startVerification({
        user_id: 'u-1',
        difficulty: 'medium',
      });

      expect(mockedPost).toHaveBeenCalledWith('/verification/start', {
        user_id: 'u-1',
        difficulty: 'medium',
      });
      expect(result.verification_id).toBe('v-1');
      expect(result.phrase).toBe('say this');
    });
  });

  describe('verifyVoice', () => {
    it('POSTs multipart with verification_id, challenge_id and audio_file', async () => {
      const blob = new Blob(['x'], { type: 'audio/wav' });
      mockedPost.mockResolvedValueOnce({
        data: {
          verification_id: 'v-1',
          user_id: 'u-1',
          is_verified: true,
          confidence_score: 0.95,
          similarity_score: 0.92,
          anti_spoofing_score: 0.1,
          phrase_match: true,
          is_live: true,
          threshold_used: 0.8,
        },
      });

      const result = await verificationService.verifyVoice({
        verification_id: 'v-1',
        challenge_id: 'c-1',
        audioBlob: blob,
      });

      const [url, fd, opts] = mockedPost.mock.calls[0]!;
      expect(url).toBe('/verification/verify');
      expect((opts as { headers: Record<string, string> }).headers['Content-Type']).toBe(
        'multipart/form-data'
      );
      const entries = Array.from((fd as FormData).entries());
      expect(entries).toEqual(
        expect.arrayContaining([
          ['verification_id', 'v-1'],
          ['challenge_id', 'c-1'],
        ])
      );
      expect(entries.find(([k]) => k === 'audio_file')).toBeDefined();
      expect(result.is_verified).toBe(true);
      expect(result.confidence_score).toBeCloseTo(0.95);
    });
  });

  describe('quickVerify', () => {
    it('POSTs multipart with user_id and audio_file to /verification/quick-verify', async () => {
      const blob = new Blob(['x'], { type: 'audio/wav' });
      mockedPost.mockResolvedValueOnce({
        data: {
          user_id: 'u-1',
          is_verified: false,
          confidence_score: 0.31,
          similarity_score: 0.3,
          anti_spoofing_score: 0.4,
          is_live: true,
          threshold_used: 0.8,
        },
      });

      const result = await verificationService.quickVerify({
        user_id: 'u-1',
        audioBlob: blob,
      });

      const [url, fd] = mockedPost.mock.calls[0]!;
      expect(url).toBe('/verification/quick-verify');
      const entries = Array.from((fd as FormData).entries());
      expect(entries).toEqual(expect.arrayContaining([['user_id', 'u-1']]));
      expect(entries.find(([k]) => k === 'audio_file')).toBeDefined();
      expect(result.is_verified).toBe(false);
    });
  });

  describe('getVerificationHistory', () => {
    it('GETs /verification/user/{userId}/history?limit=... and parses envelope', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          success: true,
          history: {
            user_id: 'u-1',
            total_attempts: 2,
            recent_attempts: [
              {
                id: '1',
                result: 'success',
                score: 95,
                date: '2024-01-01',
                method: 'Frase Aleatoria',
              },
            ],
          },
        },
      });

      const result = await verificationService.getVerificationHistory('u-1', 5);

      expect(mockedGet).toHaveBeenCalledWith('/verification/user/u-1/history', {
        params: { limit: 5 },
      });
      expect(result.history.recent_attempts).toHaveLength(1);
      expect(result.history.recent_attempts[0]!.result).toBe('success');
    });

    it('falls back to the default limit of 10', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          success: true,
          history: { user_id: 'u-1', total_attempts: 0, recent_attempts: [] },
        },
      });

      await verificationService.getVerificationHistory('u-1');

      expect(mockedGet).toHaveBeenCalledWith('/verification/user/u-1/history', {
        params: { limit: 10 },
      });
    });
  });

  describe('startMultiPhraseVerification', () => {
    it('POSTs JSON to /verification/start-multi and returns the 3 challenges', async () => {
      mockedPost.mockResolvedValueOnce({
        data: {
          verification_id: 'v-1',
          user_id: 'u-1',
          challenges: [
            {
              challenge_id: 'c-1',
              phrase: 'a',
              phrase_id: 'p-1',
              difficulty: 'medium',
              expires_at: '2024-01-01T00:00:00Z',
              expires_in_seconds: 60,
            },
            {
              challenge_id: 'c-2',
              phrase: 'b',
              phrase_id: 'p-2',
              difficulty: 'medium',
              expires_at: '2024-01-01T00:00:00Z',
              expires_in_seconds: 60,
            },
            {
              challenge_id: 'c-3',
              phrase: 'c',
              phrase_id: 'p-3',
              difficulty: 'medium',
              expires_at: '2024-01-01T00:00:00Z',
              expires_in_seconds: 60,
            },
          ],
          total_phrases: 3,
        },
      });

      const result = await verificationService.startMultiPhraseVerification({
        user_id: 'u-1',
      });

      expect(mockedPost).toHaveBeenCalledWith('/verification/start-multi', {
        user_id: 'u-1',
      });
      expect(result.challenges).toHaveLength(3);
      expect(result.total_phrases).toBe(3);
    });
  });

  describe('verifyPhrase', () => {
    it('POSTs multipart with phrase_id, phrase_number, audio_file plus device info', async () => {
      const blob = new Blob(['x'], { type: 'audio/wav' });
      mockedPost.mockResolvedValueOnce({
        data: {
          phrase_number: 1,
          individual_score: 0.91,
          is_complete: false,
          phrases_remaining: 2,
        },
      });

      const result = await verificationService.verifyPhrase({
        verification_id: 'v-1',
        challenge_id: 'c-1',
        phrase_number: 1,
        audioBlob: blob,
      });

      const [url, fd, opts] = mockedPost.mock.calls[0]!;
      expect(url).toBe('/verification/verify-phrase');
      expect((opts as { headers: Record<string, string> }).headers['Content-Type']).toBe(
        'multipart/form-data'
      );
      const entries = Array.from((fd as FormData).entries());
      expect(entries).toEqual(
        expect.arrayContaining([
          ['verification_id', 'v-1'],
          ['phrase_id', 'c-1'],
          ['phrase_number', '1'],
          ['user_agent', 'mock-user-agent'],
          ['device_info', 'mock-device-info'],
        ])
      );
      expect(entries.find(([k]) => k === 'audio_file')).toBeDefined();
      expect(result.phrase_number).toBe(1);
      expect(result.is_complete).toBe(false);
    });
  });
});
