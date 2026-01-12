import api from "./api";

interface EnrollmentStatus {
  is_enrolled: boolean;
  enrollment_status: string;
  sample_count: number;
}

interface Phrase {
  id: string;
  text: string;
  source?: string;
}

interface PhraseSession {
  session_id: string;
  phrases: Phrase[];
  purpose: string;
}

interface EnrollmentResult {
  success: boolean;
  message: string;
  sample_count?: number;
  enrollment_complete?: boolean;
}

interface EnrollmentStartResponse {
  success: boolean;
  enrollment_id: string;
  user_id: string;
  phrases: Phrase[];
  required_samples: number;
}

interface VerificationResult {
  success: boolean;
  verified: boolean;
  confidence: number;
  message: string;
  details?: {
    speaker_score?: number;
    text_score?: number;
    spoofing_score?: number;
  };
}

export const biometricService = {
  /**
   * Check if user has enrolled their voice
   */
  async getEnrollmentStatus(): Promise<EnrollmentStatus> {
    const response = await api.get<EnrollmentStatus>("/enrollment/status");
    return response.data;
  },

  /**
   * Get random phrases for enrollment or verification
   */
  async getPhrases(
    purpose: "enrollment" | "verification" = "verification",
    count: number = 3
  ): Promise<PhraseSession> {
    const response = await api.get<PhraseSession>(
      `/phrases/session?purpose=${purpose}&count=${count}`
    );
    return response.data;
  },

  /**
   * Start a new enrollment session
   */
  async startEnrollment(): Promise<EnrollmentStartResponse> {
    const response = await api.post<EnrollmentStartResponse>(
      "/enrollment/start"
    );
    return response.data;
  },

  /**
   * Submit audio for voice enrollment
   */
  async enrollAudio(
    audioBlob: Blob,
    phraseId: string,
    phraseText: string
  ): Promise<EnrollmentResult> {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    formData.append("phrase_id", phraseId);
    formData.append("phrase_text", phraseText);

    const response = await api.post<EnrollmentResult>(
      "/enrollment/audio",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Submit audio for voice verification
   */
  async verifyVoice(
    audioBlob: Blob,
    phraseId: string,
    phraseText: string
  ): Promise<VerificationResult> {
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");
    formData.append("phrase_id", phraseId);
    formData.append("phrase_text", phraseText);

    const response = await api.post<VerificationResult>(
      "/verification/voice",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },
};

export type {
  EnrollmentStatus,
  Phrase,
  PhraseSession,
  EnrollmentResult,
  VerificationResult,
  EnrollmentStartResponse,
};
export default biometricService;
