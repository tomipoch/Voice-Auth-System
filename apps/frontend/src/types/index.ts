// ============================================
// User & Auth Types
// ============================================

export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  name?: string; // Computed field from backend (first_name + last_name)
  fullName?: string; // Alias for name (backward compatibility)
  username?: string; // Alias for email or name
  role: UserRole;
  company?: string;
  rut?: string; // Chilean national ID
  isVerified?: boolean;
  voiceProfile?: VoiceProfile;
  voice_template?: VoiceTemplateInfo | null;
  createdAt?: string;
  created_at?: string; // Backend uses snake_case
  updatedAt?: string;
  settings?: {
    notifications?: {
      email?: boolean;
      push?: boolean;
      verificationAlerts?: boolean;
    };
    security?: {
      twoFactor?: boolean;
      sessionTimeout?: number;
      requireReauth?: boolean;
    };
    appearance?: {
      theme?: string;
      language?: string;
    };
  };
}

export type UserRole = 'user' | 'admin' | 'superadmin';

export interface VoiceProfile {
  id: string;
  userId: string;
  samples: number;
  quality: number;
  lastVerified: string;
  enrolledAt: string;
}

export interface VoiceTemplateInfo {
  id?: string;
  model_type?: string;
  sample_count?: number;
  created_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterData {
  first_name: string;
  last_name: string;
  rut: string;
  email: string;
  password: string;
  company?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user: User;
}

// ============================================
// Re-exports for the consolidated phrase/rule types
// ============================================
export type { Phrase, Book, PhraseStats, PhraseFilters } from './phrases';
export type { Challenge } from './phrases';
export type { PhraseRule as PhraseQualityRule } from './phraseRules';

// ============================================
// Component props (kept inline because they are small and
// only used by their sibling component files)
// ============================================

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined' | 'glass';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
}

// ============================================
// Context types
// ============================================

export interface ThemeContextType {
  theme: 'light' | 'dark';
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
}

// ============================================
// Hook returns (kept here because they are tightly
// coupled to the shared form/validation vocabulary below)
// ============================================

export type FormErrors<T> = Partial<Record<keyof T, string>>;

export interface AudioQuality {
  snr: number;
  clarity: number;
  volume: number;
  quality: 'excellent' | 'good' | 'fair' | 'poor';
}
