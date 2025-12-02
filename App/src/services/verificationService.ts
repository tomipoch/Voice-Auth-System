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
  challenge_id: string;
  phrase: string;
  phrase_id: string;
  expires_at: string;
  message: string;
}

export interface VerifyVoiceRequest {
  verification_id: string;
  challenge_id: string;
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

export interface StartMultiPhraseVerificationResponse {
  verification_id: string;
  user_id: string;
  challenges: Challenge[];
  total_phrases: number;
}

export interface Challenge {
  challenge_id: string;
  phrase: string;
  phrase_id: string;
  difficulty: string;
  expires_at: string;
  expires_in_seconds: number;
}

export interface VerifyPhraseRequest {
  verification_id: string;
  challenge_id: string;
  phrase_number: number; // 1, 2, or 3
  audioBlob: Blob;
}

export interface PhraseResult {
  phrase_number: number;
  challenge_id: string;
  similarity_score: number;
  asr_confidence: number;
  asr_penalty: number;
  final_score: number;
}

export interface VerifyPhraseResponse {
  phrase_number: number;
  individual_score: number;
  is_complete: boolean;

  // Only present if is_complete=false
  phrases_remaining?: number;

  // Only present if is_complete=true
  average_score?: number;
  is_verified?: boolean;
  threshold_used?: number;
  all_results?: PhraseResult[];

  // In case of spoof detection
  rejected?: boolean;
  reason?: string;
  anti_spoofing_score?: number;
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
   * Verificar voz con challenge específico
   */
  async verifyVoice(data: VerifyVoiceRequest): Promise<VerifyVoiceResponse> {
    const formData = new FormData();
    formData.append('verification_id', data.verification_id);
    formData.append('challenge_id', data.challenge_id);
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

  // ===== Multi-phrase verification methods =====

  /**
   * Iniciar verificación multi-frase (3 frases)
   */
  async startMultiPhraseVerification(
    data: StartVerificationRequest
  ): Promise<StartMultiPhraseVerificationResponse> {
    const response = await api.post<StartMultiPhraseVerificationResponse>(
      `${this.baseUrl}/start-multi`,
      data
    );

    return response.data;
  }

  /**
   * Verificar un challenge individual en verificación multi-frase
   */
  async verifyPhrase(data: VerifyPhraseRequest): Promise<VerifyPhraseResponse> {
    const formData = new FormData();
    formData.append('verification_id', data.verification_id);
    formData.append('challenge_id', data.challenge_id);
    formData.append('phrase_number', data.phrase_number.toString());
    formData.append('audio_file', data.audioBlob, `phrase_${data.phrase_number}.wav`);

    const response = await api.post<VerifyPhraseResponse>(
      `${this.baseUrl}/verify-phrase`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }
}

export const verificationService = new VerificationService();
export default verificationService;
