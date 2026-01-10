/**
 * Dataset Recording Service
 * Handles API calls for controlling dataset audio recording
 */

import api from './api';

export interface RecordingStatus {
  enabled: boolean;
  session_id?: string;
  session_dir?: string;
  total_users: number;
  total_enrollment_audios: number;
  total_verification_audios: number;
  users: Record<
    string,
    {
      username: string;
      email?: string;
      enrollment_count: number;
      verification_count: number;
    }
  >;
}

export interface StartRecordingResponse {
  success: boolean;
  session_id: string;
  session_dir: string;
  message: string;
}

export interface StopRecordingResponse {
  success: boolean;
  session_dir?: string;
  message: string;
}

export const datasetRecordingService = {
  /**
   * Get current recording status
   */
  async getStatus(): Promise<RecordingStatus> {
    const response = await api.get('/dataset-recording/status');
    return response.data;
  },

  /**
   * Start dataset recording session
   */
  async startRecording(sessionName: string): Promise<StartRecordingResponse> {
    const response = await api.post('/dataset-recording/start', { session_name: sessionName });
    return response.data;
  },

  /**
   * Stop dataset recording session
   */
  async stopRecording(): Promise<StopRecordingResponse> {
    const response = await api.post('/dataset-recording/stop');
    return response.data;
  },
};

export default datasetRecordingService;
