/**
 * Phrase Service
 * API service for phrase management
 */

import api from './api';
import type {
  Phrase,
  Book,
  PhraseStats,
  PhraseFilters,
  PhraseListResponse,
  UpdatePhraseStatusRequest,
  UpdatePhraseStatusResponse,
  DeletePhraseResponse,
} from '../types/phrases';

class PhraseService {
  private readonly baseUrl = '/phrases';

  /**
   * Get phrase statistics
   */
  async getStats(language = 'es'): Promise<PhraseStats> {
    const response = await api.get<PhraseStats>(`${this.baseUrl}/stats`, {
      params: { language },
    });
    return response.data;
  }

  /**
   * Get paginated list of phrases with filters
   */
  async getPhrases(filters: PhraseFilters): Promise<PhraseListResponse> {
    const params: Record<string, string | number | boolean | undefined> = {
      page: filters.page,
      limit: filters.limit,
    };

    if (filters.difficulty) {
      params.difficulty = filters.difficulty;
    }

    if (filters.is_active !== null && filters.is_active !== undefined) {
      params.is_active = filters.is_active;
    }

    if (filters.search) {
      params.search = filters.search;
    }

    if (filters.book_id) {
      params.book_id = filters.book_id;
    }

    if (filters.author) {
      params.author = filters.author;
    }

    const response = await api.get<PhraseListResponse>(`${this.baseUrl}/list`, {
      params,
    });
    return response.data;
  }

  /**
   * Get random phrases
   */
  async getRandomPhrases(count = 1, difficulty?: string, language = 'es'): Promise<Phrase[]> {
    const response = await api.get<Phrase[]>(`${this.baseUrl}/random`, {
      params: { count, difficulty, language },
    });
    return response.data;
  }

  /**
   * Toggle phrase active status
   */
  async togglePhraseStatus(
    phraseId: string,
    isActive: boolean
  ): Promise<UpdatePhraseStatusResponse> {
    const response = await api.patch<UpdatePhraseStatusResponse>(
      `${this.baseUrl}/${phraseId}/status`,
      { is_active: isActive } as UpdatePhraseStatusRequest
    );
    return response.data;
  }

  /**
   * Delete a phrase
   */
  async deletePhrase(phraseId: string): Promise<DeletePhraseResponse> {
    const response = await api.delete<DeletePhraseResponse>(`${this.baseUrl}/${phraseId}`);
    return response.data;
  }

  /**
   * Get a list of books
   */
  async getBooks(): Promise<Book[]> {
    const response = await api.get('/phrases/books');
    return response.data;
  }
}

export const phraseService = new PhraseService();
export default phraseService;
