/**
 * Enrollment Service - Dynamic Phrases Integration
 * Servicio para gestionar el proceso de enrollment con frases dinámicas
 */

import api from './api';

export interface Phrase {
  id: string;
  text: string;
  difficulty: string;
  word_count: number;
}

export interface StartEnrollmentRequest {
  external_ref?: string;
  user_id?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}

export interface StartEnrollmentResponse {
  success: boolean;
  enrollment_id: string;
  user_id: string;
  phrases: Phrase[];
  required_samples: number;
  message: string;
}

export interface AddSampleResponse {
  success: boolean;
  sample_id: string;
  samples_completed: number;
  samples_required: number;
  is_complete: boolean;
  next_phrase: Phrase | null;
  quality_score?: number;
  message: string;
}

export interface CompleteEnrollmentResponse {
  success: boolean;
  voiceprint_id: string;
  user_id: string;
  enrollment_quality: number;
  samples_used: number;
  message: string;
}

export interface EnrollmentStatusResponse {
  status: 'not_started' | 'in_progress' | 'enrolled' | 'user_not_found';
  voiceprint_id?: string;
  created_at?: string;
  samples_count: number;
  required_samples: number;
  phrases_used?: Array<{
    phrase_id: string;
    phrase_text: string;
    used_at: string;
  }>;
}

class EnrollmentService {
  private readonly baseUrl = '/enrollment';

  /**
   * Iniciar proceso de enrollment
   */
  async startEnrollment(data: StartEnrollmentRequest): Promise<StartEnrollmentResponse> {
    const formData = new FormData();

    if (data.external_ref) {
      formData.append('external_ref', data.external_ref);
    }
    if (data.user_id) {
      formData.append('user_id', data.user_id);
    }
    if (data.difficulty) {
      formData.append('difficulty', data.difficulty);
    }

    const response = await api.post<StartEnrollmentResponse>(`${this.baseUrl}/start`, formData);

    return response.data;
  }

  /**
   * Agregar muestra de audio con frase
   */
  async addSample(
    enrollmentId: string,
    phraseId: string,
    audioBlob: Blob
  ): Promise<AddSampleResponse> {
    const formData = new FormData();
    formData.append('enrollment_id', enrollmentId);
    formData.append('phrase_id', phraseId);
    formData.append('audio_file', audioBlob, 'enrollment_sample.wav');

    const response = await api.post<AddSampleResponse>(`${this.baseUrl}/add-sample`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Completar enrollment y crear voiceprint
   */
  async completeEnrollment(
    enrollmentId: string,
    speakerModelId?: number
  ): Promise<CompleteEnrollmentResponse> {
    const formData = new FormData();
    formData.append('enrollment_id', enrollmentId);

    if (speakerModelId !== undefined) {
      formData.append('speaker_model_id', speakerModelId.toString());
    }

    const response = await api.post<CompleteEnrollmentResponse>(
      `${this.baseUrl}/complete`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Obtener estado del enrollment de un usuario
   */
  async getEnrollmentStatus(userId: string): Promise<EnrollmentStatusResponse> {
    const response = await api.get<EnrollmentStatusResponse>(`${this.baseUrl}/status/${userId}`);

    return response.data;
  }
}

export const enrollmentService = new EnrollmentService();
export default enrollmentService;
