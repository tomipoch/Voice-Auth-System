import { z } from 'zod';

// ============================================
// Auth Schemas
// ============================================

export const loginSchema = z.object({
  email: z.string().email('Email inválido').min(1, 'El email es requerido'),
  password: z
    .string()
    .min(8, 'La contraseña debe tener al menos 8 caracteres')
    .regex(/[A-Z]/, 'Debe contener al menos una mayúscula')
    .regex(/[a-z]/, 'Debe contener al menos una minúscula')
    .regex(/[0-9]/, 'Debe contener al menos un número')
    .regex(/[^A-Za-z0-9]/, 'Debe contener al menos un carácter especial'),
  rememberMe: z.boolean().optional(),
});

export const registerSchema = z
  .object({
    email: z.string().email('Email inválido').min(1, 'El email es requerido'),
    username: z
      .string()
      .min(3, 'El nombre de usuario debe tener al menos 3 caracteres')
      .max(20, 'El nombre de usuario no puede tener más de 20 caracteres')
      .regex(/^[a-zA-Z0-9_]+$/, 'Solo letras, números y guiones bajos'),
    fullName: z
      .string()
      .min(2, 'El nombre completo es requerido')
      .max(100, 'Nombre demasiado largo'),
    password: z
      .string()
      .min(8, 'La contraseña debe tener al menos 8 caracteres')
      .regex(/[A-Z]/, 'Debe contener al menos una mayúscula')
      .regex(/[a-z]/, 'Debe contener al menos una minúscula')
      .regex(/[0-9]/, 'Debe contener al menos un número')
      .regex(/[^A-Za-z0-9]/, 'Debe contener al menos un carácter especial'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Las contraseñas no coinciden',
    path: ['confirmPassword'],
  });

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;

// ============================================
// User Schemas
// ============================================

export const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  username: z.string().min(3).max(20),
  fullName: z.string().min(2).max(100),
  role: z.enum(['user', 'admin', 'super_admin']),
  isVerified: z.boolean(),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export const updateUserSchema = z.object({
  email: z.string().email().optional(),
  username: z.string().min(3).max(20).optional(),
  fullName: z.string().min(2).max(100).optional(),
});

export type UserValidation = z.infer<typeof userSchema>;
export type UpdateUserData = z.infer<typeof updateUserSchema>;

// ============================================
// Voice Enrollment Schemas
// ============================================

export const audioMetadataSchema = z.object({
  duration: z.number().min(1).max(30),
  size: z.number().max(10 * 1024 * 1024), // 10MB max
  mimeType: z.string().regex(/^audio\/(wav|mp3|webm|ogg)$/),
  sampleRate: z.number().optional(),
  channels: z.number().optional(),
});

export const enrollmentDataSchema = z.object({
  userId: z.string().uuid(),
  samples: z.array(z.instanceof(Blob)).min(3).max(5),
  metadata: z.array(audioMetadataSchema),
});

export type AudioMetadata = z.infer<typeof audioMetadataSchema>;
export type EnrollmentValidation = z.infer<typeof enrollmentDataSchema>;

// ============================================
// Settings Schemas
// ============================================

export const settingsSchema = z.object({
  theme: z.enum(['light', 'dark']),
  language: z.enum(['es', 'en']),
  notifications: z.boolean(),
  soundEnabled: z.boolean(),
  autoSave: z.boolean(),
});

export type SettingsData = z.infer<typeof settingsSchema>;

// ============================================
// Search & Filter Schemas
// ============================================

export const searchQuerySchema = z.object({
  query: z.string().max(500).optional(),
  page: z.number().int().positive().default(1),
  limit: z.number().int().min(1).max(100).default(10),
  sort: z.string().optional(),
  order: z.enum(['asc', 'desc']).optional(),
});

export type SearchQuery = z.infer<typeof searchQuerySchema>;

// ============================================
// API Response Schemas
// ============================================

export const apiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema,
    message: z.string().optional(),
  });

export const paginatedResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    data: z.array(dataSchema),
    pagination: z.object({
      page: z.number(),
      limit: z.number(),
      total: z.number(),
      totalPages: z.number(),
    }),
  });

// ============================================
// Validation Utilities
// ============================================

export const validateData = <T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; errors: z.ZodError } => {
  const result = schema.safeParse(data);

  if (result.success) {
    return { success: true, data: result.data };
  }

  return { success: false, errors: result.error };
};

export const getValidationErrors = (error: z.ZodError): Record<string, string> => {
  const errors: Record<string, string> = {};

  error.issues.forEach((err) => {
    const path = err.path.join('.');
    errors[path] = err.message;
  });

  return errors;
};

// ============================================
// Custom Validators
// ============================================

export const isStrongPassword = (password: string): boolean => {
  const minLength = 8;
  const hasUpperCase = /[A-Z]/.test(password);
  const hasLowerCase = /[a-z]/.test(password);
  const hasNumber = /[0-9]/.test(password);
  const hasSpecialChar = /[^A-Za-z0-9]/.test(password);

  return (
    password.length >= minLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar
  );
};

export const isValidUsername = (username: string): boolean => {
  return /^[a-zA-Z0-9_]{3,20}$/.test(username);
};

export const isValidEmail = (email: string): boolean => {
  return z.string().email().safeParse(email).success;
};

export const isValidUrl = (url: string): boolean => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};
