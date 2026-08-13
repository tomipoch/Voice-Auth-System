/**
 * Unit tests for the typed EnrollmentService.
 *
 * Mirrors the authService.test.ts pattern: axios is replaced via
 * vi.mock('../api'), so each call is asserted against the URL +
 * FormData payload it should produce and the response shape it
 * should return.
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
import { enrollmentService } from '../enrollmentService';

const mockedPost = vi.mocked(api.post);
const mockedGet = vi.mocked(api.get);

describe('enrollmentService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startEnrollment', () => {
    it('POSTs to /enrollment/start with all form fields when provided', async () => {
      mockedPost.mockResolvedValueOnce({
        data: {
          success: true,
          enrollment_id: 'enroll-1',
          user_id: 'u-1',
          challenges: [],
          required_samples: 3,
          message: 'started',
          voiceprint_exists: false,
        },
      });

      const result = await enrollmentService.startEnrollment({
        user_id: 'u-1',
        external_ref: 'ext-1',
        difficulty: 'hard',
        force_overwrite: true,
      });

      expect(mockedPost).toHaveBeenCalledTimes(1);
      const [url, formData] = mockedPost.mock.calls[0]!;
      expect(url).toBe('/enrollment/start');
      const entries = Array.from((formData as FormData).entries());
      expect(entries).toEqual(
        expect.arrayContaining([
          ['user_id', 'u-1'],
          ['external_ref', 'ext-1'],
          ['difficulty', 'hard'],
          ['force_overwrite', 'true'],
        ]),
      );
      expect(result.enrollment_id).toBe('enroll-1');
      expect(result.voiceprint_exists).toBe(false);
    });

    it('omits optional fields and defaults difficulty to medium', async () => {
      mockedPost.mockResolvedValueOnce({
        data: {
          success: true,
          enrollment_id: 'enroll-2',
          user_id: 'u-2',
          challenges: [],
          required_samples: 3,
          message: 'started',
        },
      });

      await enrollmentService.startEnrollment({});

      const [, formData] = mockedPost.mock.calls[0]!;
      const entries = Array.from((formData as FormData).entries());
      expect(entries).toEqual([['difficulty', 'medium']]);
    });
  });

  describe('addSample', () => {
    it('POSTs multipart with enrollment_id, challenge_id, audio_file', async () => {
      const blob = new Blob(['x'], { type: 'audio/wav' });
      mockedPost.mockResolvedValueOnce({
        data: {
          success: true,
          sample_id: 's-1',
          samples_completed: 1,
          samples_required: 3,
          is_complete: false,
          next_challenge: {
            challenge_id: 'c-2',
            phrase: 'say',
            phrase_id: 'p-2',
            difficulty: 'medium',
            expires_at: '2024-01-01T00:00:00Z',
            expires_in_seconds: 60,
          },
          quality_score: 0.9,
          message: 'sample stored',
        },
      });

      const result = await enrollmentService.addSample('enroll-1', 'c-1', blob);

      const [url, fd, opts] = mockedPost.mock.calls[0]!;
      expect(url).toBe('/enrollment/add-sample');
      expect((opts as { headers: { 'Content-Type': string } }).headers['Content-Type']).toBe(
        'multipart/form-data',
      );
      const entries = Array.from((fd as FormData).entries());
      expect(entries).toEqual(
        expect.arrayContaining([
          ['enrollment_id', 'enroll-1'],
          ['challenge_id', 'c-1'],
        ]),
      );
      expect(entries.find(([k]) => k === 'audio_file')).toBeDefined();
      expect(result.next_challenge?.challenge_id).toBe('c-2');
      expect(result.is_complete).toBe(false);
    });
  });

  describe('completeEnrollment', () => {
    it('POSTs /enrollment/complete with enrollment_id only', async () => {
      mockedPost.mockResolvedValueOnce({
        data: {
          success: true,
          voiceprint_id: 'vp-1',
          user_id: 'u-1',
          enrollment_quality: 0.92,
          samples_used: 3,
          message: 'enrolled',
        },
      });

      const result = await enrollmentService.completeEnrollment('enroll-1');

      expect(result.voiceprint_id).toBe('vp-1');
      const [, fd] = mockedPost.mock.calls[0]!;
      const entries = Array.from((fd as FormData).entries());
      expect(entries).toEqual([['enrollment_id', 'enroll-1']]);
    });

    it('appends speaker_model_id when provided', async () => {
      mockedPost.mockResolvedValueOnce({
        data: {
          success: true,
          voiceprint_id: 'vp-1',
          user_id: 'u-1',
          enrollment_quality: 0.95,
          samples_used: 3,
          message: 'enrolled',
        },
      });

      await enrollmentService.completeEnrollment('enroll-1', 7);

      const [, fd] = mockedPost.mock.calls[0]!;
      const entries = Array.from((fd as FormData).entries());
      expect(entries).toEqual([
        ['enrollment_id', 'enroll-1'],
        ['speaker_model_id', '7'],
      ]);
    });
  });

  describe('getEnrollmentStatus', () => {
    it('GETs /enrollment/status/{userId}', async () => {
      mockedGet.mockResolvedValueOnce({
        data: {
          status: 'in_progress',
          samples_count: 1,
          required_samples: 3,
          phrases_used: [
            { phrase_id: 'p-1', phrase_text: 'hola mundo', used_at: '2024-01-01T00:00:00Z' },
          ],
        },
      });

      const result = await enrollmentService.getEnrollmentStatus('u-1');

      expect(mockedGet).toHaveBeenCalledWith('/enrollment/status/u-1');
      expect(result.status).toBe('in_progress');
      expect(result.phrases_used?.[0]?.phrase_id).toBe('p-1');
    });
  });
});
