/**
 * Phrase Types
 * TypeScript interfaces for phrase management
 */

export interface Phrase {
  id: string;
  text: string;
  source?: string;
  book_title?: string;
  book_author?: string;
  word_count: number;
  char_count: number;
  language: string;
  difficulty: 'easy' | 'medium' | 'hard';
  is_active: boolean;
  created_at: string;
  phoneme_score?: number;
  style?: 'narrative' | 'descriptive' | 'dialogue' | 'poetic';
}

export interface Book {
  id: string;
  title: string;
  author?: string;
}

export interface PhraseStats {
  total: number;
  active: number;
  inactive: number;
  easy: number;
  medium: number;
  hard: number;
  language: string;
}

export interface PhraseFilters {
  page?: number;
  limit?: number;
  difficulty?: string;
  is_active?: boolean;
  search?: string;
  book_id?: string;
  author?: string;
}

export interface PhraseListResponse {
  phrases: Phrase[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface UpdatePhraseStatusRequest {
  is_active: boolean;
}

export interface UpdatePhraseStatusResponse {
  success: boolean;
  message: string;
  phrase_id: string;
  is_active: boolean;
}

export interface DeletePhraseResponse {
  success: boolean;
  message: string;
  phrase_id: string;
}

export interface UpdatePhraseTextRequest {
  text: string;
}

export interface UpdatePhraseTextResponse {
  success: boolean;
  message: string;
  phrase_id: string;
  text: string;
  word_count: number;
  char_count: number;
}
