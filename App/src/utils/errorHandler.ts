import toast from 'react-hot-toast';
import { AxiosError } from 'axios';

export interface AppError {
  message: string;
  code?: string;
  statusCode?: number;
  details?: unknown;
  timestamp: string;
}

export class ErrorHandler {
  /**
   * Handle any type of error and convert to AppError
   */
  static handle(error: unknown): AppError {
    const timestamp = new Date().toISOString();

    if (error instanceof Error) {
      return {
        message: error.message,
        details: error.stack,
        timestamp,
      };
    }

    if (typeof error === 'string') {
      return {
        message: error,
        timestamp,
      };
    }

    return {
      message: 'Error desconocido',
      details: error,
      timestamp,
    };
  }

  /**
   * Handle API/HTTP errors from Axios
   */
  static handleApiError(error: unknown): AppError {
    const timestamp = new Date().toISOString();

    if (this.isAxiosError(error)) {
      const statusCode = error.response?.status;
      const message = (error.response?.data as { message?: string })?.message || error.message;
      const code = error.code;

      // Show user-friendly toast notifications
      switch (statusCode) {
        case 400:
          toast.error('Solicitud inválida. Verifica los datos ingresados.');
          break;
        case 401:
          toast.error('No autorizado. Por favor inicia sesión nuevamente.');
          // Could trigger logout here
          break;
        case 403:
          toast.error('Acceso denegado. No tienes permisos para esta acción.');
          break;
        case 404:
          toast.error('Recurso no encontrado.');
          break;
        case 409:
          toast.error('Conflicto. El recurso ya existe.');
          break;
        case 422:
          toast.error('Datos de validación incorrectos.');
          break;
        case 429:
          toast.error('Demasiadas solicitudes. Intenta más tarde.');
          break;
        case 500:
          toast.error('Error del servidor. Intenta nuevamente.');
          break;
        case 503:
          toast.error('Servicio no disponible. Intenta más tarde.');
          break;
        default:
          if (code === 'ECONNABORTED') {
            toast.error('Tiempo de espera agotado. Verifica tu conexión.');
          } else if (code === 'ERR_NETWORK') {
            toast.error('Error de red. Verifica tu conexión a internet.');
          } else {
            toast.error(message || 'Error de conexión');
          }
      }

      return {
        message,
        statusCode,
        code,
        details: error.response?.data,
        timestamp,
      };
    }

    // Fallback for non-Axios errors
    return this.handle(error);
  }

  /**
   * Type guard for Axios errors
   */
  private static isAxiosError(error: unknown): error is AxiosError {
    return (error as AxiosError).isAxiosError === true;
  }

  /**
   * Log error to console (and future: external service)
   */
  static log(error: AppError, context?: string): void {
    const logData = {
      ...error,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    console.error('[ErrorHandler]', logData);

    // TODO: Send to external logging service (Sentry, LogRocket, etc.)
    // if (process.env.NODE_ENV === 'production') {
    //   Sentry.captureException(error);
    // }
  }

  /**
   * Handle validation errors from forms
   */
  static handleValidationError(errors: Record<string, string[]>): void {
    const firstError = Object.values(errors)[0]?.[0];
    if (firstError) {
      toast.error(firstError);
    }
  }

  /**
   * Create a user-friendly error message
   */
  static getUserMessage(error: AppError): string {
    // Map technical errors to user-friendly messages
    const errorMessages: Record<string, string> = {
      'Network Error': 'No se pudo conectar al servidor. Verifica tu conexión.',
      timeout: 'La solicitud tardó demasiado. Intenta nuevamente.',
      ECONNABORTED: 'Tiempo de espera agotado.',
      ERR_NETWORK: 'Error de red. Verifica tu conexión.',
    };

    return errorMessages[error.code || ''] || error.message;
  }
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: Error | undefined = undefined;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (i < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, i);
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError ?? new Error('Max retries exceeded with unknown error');
}

export default ErrorHandler;
