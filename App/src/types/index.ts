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
  voice_template?: boolean; // Backend returns this
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

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
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

// Legacy support - puede ser removido después
export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  expires_in?: number;
}

// ============================================
// API Types
// ============================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ApiError {
  success: false;
  message: string;
  errors?: Record<string, string[]>;
  statusCode: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface QueryParams {
  page?: number;
  limit?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  search?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface Phrase {
  id: string;
  text: string;
  source?: string;
  word_count: number;
  char_count: number;
  language: string;
  difficulty: string;
  is_active: boolean;
  created_at: string;
}

export interface Challenge {
  challenge_id: string;
  phrase: string;
  phrase_id: string;
  difficulty: string;
  expires_at: string;
  expires_in_seconds: number;
}

export interface PhraseStats {
  total: number;
  easy: number;
  medium: number;
  hard: number;
  language: string;
}

export interface PhraseQualityRule {
  id: string;
  rule_name: string;
  rule_type: 'threshold' | 'rate_limit' | 'cleanup';
  rule_value: number;
  is_active: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}

// ============================================
// Voice Processing Types
// ============================================

export interface AudioRecording {
  blob: Blob;
  url: string;
  duration: number;
  size: number;
  mimeType: string;
}

export interface AudioQuality {
  snr: number; // Signal-to-Noise Ratio
  clarity: number;
  volume: number;
  quality: 'excellent' | 'good' | 'fair' | 'poor';
}

export interface EnrollmentStep {
  id: number;
  title: string;
  description: string;
  sampleRequired: boolean;
  completed: boolean;
}

export interface EnrollmentData {
  userId: string;
  samples: AudioRecording[];
  currentStep: number;
  totalSteps: number;
  progress: number;
}

export interface VerificationResult {
  verified: boolean;
  confidence: number;
  userId: string;
  timestamp: string;
  audioQuality: AudioQuality;
}

// ============================================
// Dashboard & Stats Types
// ============================================

export interface DashboardStats {
  totalUsers: number;
  activeUsers: number;
  totalVerifications: number;
  successRate: number;
  avgConfidence: number;
  recentActivity: Activity[];
  avgResponseTime?: number;
  systemUptime?: number;
}

export interface Activity {
  id: string;
  type: 'enrollment' | 'verification' | 'login' | 'logout';
  userId: string;
  username: string;
  timestamp: string;
  success: boolean;
  details?: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  storage: number;
  uptime: number;
  requests: number;
  errors: number;
}

// ============================================
// Component Props Types
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
// Form & Validation Types
// ============================================

export interface FormFieldError {
  field: string;
  message: string;
}

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  custom?: (value: unknown) => boolean | string;
}

export type FormErrors<T> = Partial<Record<keyof T, string>>;

export interface FormState<T> {
  values: T;
  errors: FormErrors<T>;
  touched: Partial<Record<keyof T, boolean>>;
  isSubmitting: boolean;
  isValid: boolean;
}

// ============================================
// Context Types
// ============================================

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateUser: (user: Partial<User>) => void;
}

export interface ThemeContextType {
  theme: 'light' | 'dark';
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
}

export interface SettingsModalContextType {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
}

// ============================================
// Storage Types
// ============================================

export interface StorageService {
  get: <T>(key: string) => T | null;
  set: <T>(key: string, value: T) => void;
  remove: (key: string) => void;
  clear: () => void;
}

export interface SecureStorageOptions {
  encrypt?: boolean;
  expiresIn?: number; // milliseconds
}

// ============================================
// Hook Return Types
// ============================================

export interface UseAudioRecordingReturn {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioUrl: string | null;
  audioBlob: Blob | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<void>;
  pauseRecording: () => void;
  resumeRecording: () => void;
  cancelRecording: () => void;
  error: string | null;
}

export interface UseDashboardStatsReturn {
  stats: DashboardStats | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export interface UseAuthReturn extends AuthContextType {
  hasRole: (role: UserRole | UserRole[]) => boolean;
  can: (permission: string) => boolean;
}

// ============================================
// Utility Types
// ============================================

export type Nullable<T> = T | null;
export type Optional<T> = T | undefined;
export type Maybe<T> = T | null | undefined;

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<T, Exclude<keyof T, Keys>> &
  {
    [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>>;
  }[Keys];

export type WithRequired<T, K extends keyof T> = T & { [P in K]-?: T[P] };

export type ValueOf<T> = T[keyof T];

// ============================================
// Event Types
// ============================================

export interface AudioProcessorEvent {
  type: 'start' | 'stop' | 'pause' | 'resume' | 'data' | 'error';
  data?: unknown;
  timestamp: number;
}

export interface WebSocketMessage {
  type: string;
  payload: unknown;
  timestamp: number;
}

// ============================================
// Configuration Types
// ============================================

export interface AppConfig {
  apiUrl: string;
  env: 'development' | 'staging' | 'production';
  enableMock: boolean;
  appName: string;
  appVersion: string;
}

export interface AudioConfig {
  sampleRate: number;
  channelCount: number;
  echoCancellation: boolean;
  noiseSuppression: boolean;
  autoGainControl: boolean;
}
