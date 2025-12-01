/**
 * Verification Service - Dynamic Phrases Integration
 * Servicio para gestionar el proceso de verificación con frases dinámicas
 */

import api from './api';

export interface Phrase {
  id: string;
  text: string;
  difficulty: string;
  word_count: number;
}

export interface StartVerificationRequest {
  user_id: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}

export interface StartVerificationResponse {
  success: boolean;
  verification_id: string;
  user_id: string;
  phrase: Phrase;
  message: string;
}

export interface VerifyVoiceRequest {
  verification_id: string;
  phrase_id: string;
  audioBlob: Blob;
}

export interface VerifyVoiceResponse {
  verification_id: string;
  user_id: string;
  is_verified: boolean;
  confidence_score: number;
  similarity_score: number;
  anti_spoofing_score: number | null;
  phrase_match: boolean;
  is_live: boolean;
  threshold_used: number;
}

export interface QuickVerifyRequest {
  user_id: string;
  audioBlob: Blob;
}

export interface QuickVerifyResponse {
  user_id: string;
  is_verified: boolean;
  confidence_score: number;
  similarity_score: number;
  anti_spoofing_score: number | null;
  is_live: boolean;
  threshold_used: number;
}

export interface VerificationHistoryItem {
  verification_id: string;
  is_verified: boolean;
  confidence_score: number;
  timestamp: string;
  phrase_used?: string;
}

export interface VerificationHistoryResponse {
  user_id: string;
  total_attempts: number;
  recent_attempts: VerificationHistoryItem[];
}

class VerificationService {
  private readonly baseUrl = '/verification';

  /**
   * Iniciar proceso de verificación y obtener frase
   */
  async startVerification(data: StartVerificationRequest): Promise<StartVerificationResponse> {
    const response = await api.post<StartVerificationResponse>(`${this.baseUrl}/start`, data);

    return response.data;
  }

  /**
   * Verificar voz con frase específica
   */
  async verifyVoice(data: VerifyVoiceRequest): Promise<VerifyVoiceResponse> {
    const formData = new FormData();
    formData.append('verification_id', data.verification_id);
    formData.append('phrase_id', data.phrase_id);
    formData.append('audio_file', data.audioBlob, 'verification_audio.wav');

    const response = await api.post<VerifyVoiceResponse>(`${this.baseUrl}/verify`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Verificación rápida sin gestión de frases
   */
  async quickVerify(data: QuickVerifyRequest): Promise<QuickVerifyResponse> {
    const formData = new FormData();
    formData.append('user_id', data.user_id);
    formData.append('audio_file', data.audioBlob, 'quick_verify.wav');

    const response = await api.post<QuickVerifyResponse>(`${this.baseUrl}/quick-verify`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  /**
   * Obtener historial de verificaciones
   */
  async getVerificationHistory(
    userId: string,
    limit: number = 10
  ): Promise<VerificationHistoryResponse> {
    const response = await api.get<VerificationHistoryResponse>(
      `${this.baseUrl}/history/${userId}`,
      {
        params: { limit },
      }
    );

    return response.data;
  }
}

export const verificationService = new VerificationService();
export default verificationService;
