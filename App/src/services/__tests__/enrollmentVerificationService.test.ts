import { describe, it, expect, vi, beforeEach } from 'vitest';
import { enrollmentService, verificationService } from '../apiServices';
import api from '../api';

// Mock the api module
vi.mock('../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('enrollmentService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startEnrollment', () => {
    it('successfully starts enrollment', async () => {
      const mockResponse = {
        data: {
          enrollment_id: 'enroll-123',
          user_id: 'user-1',
          samples_required: 5,
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await enrollmentService.startEnrollment('user-1');

      expect(api.post).toHaveBeenCalledWith('/enrollment/start', {
        user_id: 'user-1',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('submitAudio', () => {
    it('successfully submits audio sample', async () => {
      const mockBlob = new Blob(['audio data'], { type: 'audio/wav' });
      const mockResponse = {
        data: {
          success: true,
          sample_id: 'sample-123',
          quality_score: 95,
          samples_recorded: 1,
          samples_required: 5,
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await enrollmentService.submitAudio(
        'enroll-123',
        mockBlob,
        'Test phrase'
      );

      expect(api.post).toHaveBeenCalled();
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('completeEnrollment', () => {
    it('successfully completes enrollment', async () => {
      const mockResponse = {
        data: {
          success: true,
          voice_template_id: 'template-123',
          message: 'Enrollment completed',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await enrollmentService.completeEnrollment('enroll-123');

      expect(api.post).toHaveBeenCalledWith('/enrollment/complete/enroll-123');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getEnrollmentProgress', () => {
    it('successfully retrieves enrollment progress', async () => {
      const mockResponse = {
        data: {
          status: 'in_progress',
          samples_recorded: 3,
          samples_required: 5,
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await enrollmentService.getEnrollmentProgress('enroll-123');

      expect(api.get).toHaveBeenCalledWith('/enrollment/status/enroll-123');
      expect(result).toEqual(mockResponse.data);
    });
  });
});

describe('verificationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startVerification', () => {
    it('successfully starts verification', async () => {
      const mockResponse = {
        data: {
          verification_id: 'verify-123',
          user_id: 'user-1',
          phrase: 'Test verification phrase',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await verificationService.startVerification('user-1');

      expect(api.post).toHaveBeenCalledWith('/verification/start', {
        user_id: 'user-1',
      });
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('verifyAudio', () => {
    it('successfully verifies audio', async () => {
      const mockBlob = new Blob(['audio data'], { type: 'audio/wav' });
      const mockResponse = {
        data: {
          success: true,
          verified: true,
          confidence: 0.95,
          message: 'Verification successful',
        },
      };

      vi.mocked(api.post).mockResolvedValue(mockResponse);

      const result = await verificationService.verifyAudio(
        'verify-123',
        mockBlob,
        'Test phrase'
      );

      expect(api.post).toHaveBeenCalled();
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getVerificationResult', () => {
    it('successfully retrieves verification result', async () => {
      const mockResponse = {
        data: {
          success: true,
          confidence: 0.92,
          message: 'Verification successful',
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await verificationService.getVerificationResult('verify-123');

      expect(api.get).toHaveBeenCalledWith('/verification/result/verify-123');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getVerificationHistory', () => {
    it('successfully retrieves verification history', async () => {
      const mockResponse = {
        data: {
          success: true,
          history: [
            { id: 1, result: 'success', score: 95, date: '2024-01-01' },
            { id: 2, result: 'failure', score: 45, date: '2024-01-02' },
          ],
        },
      };

      vi.mocked(api.get).mockResolvedValue(mockResponse);

      const result = await verificationService.getVerificationHistory('user-1', 10);

      expect(api.get).toHaveBeenCalledWith('/verification/user/user-1/history?limit=10');
      expect(result).toEqual(mockResponse.data);
    });
  });
});
