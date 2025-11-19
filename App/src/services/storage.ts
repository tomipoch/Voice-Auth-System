/**
 * Storage Service
 * Maneja localStorage con prefijos por ambiente y funcionalidades adicionales
 */

import { authConfig, appConfig, features, logger } from '../config/environment.js';
import type { User } from '../types/index.js';

interface StorageUsage {
  keysCount: number;
  totalSizeBytes: number;
  totalSizeKB: number;
  keys: string[];
}

/**
 * Servicio centralizado de storage
 */
export const storageService = {
  /**
   * Obtiene la clave completa con prefijo
   */
  getKey(key: string): string {
    return `${authConfig.storagePrefix}${key}`;
  },

  /**
   * Guarda un elemento en localStorage
   */
  setItem<T>(key: string, value: T): boolean {
    try {
      const fullKey = this.getKey(key);
      const serializedValue = JSON.stringify(value);
      localStorage.setItem(fullKey, serializedValue);

      if (features.consoleLogs && appConfig.debug) {
        logger.debug('Storage SET:', { key: fullKey, value });
      }
      return true;
    } catch (error) {
      logger.error('Error saving to storage:', error);
      return false;
    }
  },

  /**
   * Obtiene un elemento de localStorage
   */
  getItem<T>(key: string): T | null {
    try {
      const fullKey = this.getKey(key);
      const item = localStorage.getItem(fullKey);

      if (!item) {
        return null;
      }

      const parsed = JSON.parse(item) as T;

      if (features.consoleLogs && appConfig.debug) {
        logger.debug('Storage GET:', { key: fullKey, value: parsed });
      }

      return parsed;
    } catch (error) {
      logger.error('Error reading from storage:', error);
      return null;
    }
  },

  /**
   * Elimina un elemento de localStorage
   */
  removeItem(key: string): boolean {
    try {
      const fullKey = this.getKey(key);
      localStorage.removeItem(fullKey);

      if (features.consoleLogs && appConfig.debug) {
        logger.debug('Storage REMOVE:', { key: fullKey });
      }
      return true;
    } catch (error) {
      logger.error('Error removing from storage:', error);
      return false;
    }
  },

  /**
   * Limpia todos los elementos con el prefijo actual
   */
  clear(): boolean {
    try {
      const keys = Object.keys(localStorage);
      const prefixKeys = keys.filter((key) => key.startsWith(authConfig.storagePrefix));

      prefixKeys.forEach((key) => {
        localStorage.removeItem(key);
      });

      if (features.consoleLogs && appConfig.debug) {
        logger.debug('Storage CLEAR:', { removedKeys: prefixKeys.length });
      }
      return true;
    } catch (error) {
      logger.error('Error clearing storage:', error);
      return false;
    }
  },

  /**
   * Verifica si existe una clave
   */
  hasItem(key: string): boolean {
    const fullKey = this.getKey(key);
    return localStorage.getItem(fullKey) !== null;
  },

  /**
   * Obtiene todas las claves con el prefijo actual
   */
  getAllKeys(): string[] {
    const keys = Object.keys(localStorage);
    return keys
      .filter((key) => key.startsWith(authConfig.storagePrefix))
      .map((key) => key.replace(authConfig.storagePrefix, ''));
  },

  /**
   * Obtiene estadísticas de uso del storage
   */
  getUsage(): StorageUsage {
    const allKeys = this.getAllKeys();
    const totalSize = allKeys.reduce((size, key) => {
      const value = this.getItem(key);
      return size + JSON.stringify(value).length;
    }, 0);

    return {
      keysCount: allKeys.length,
      totalSizeBytes: totalSize,
      totalSizeKB: Math.round((totalSize / 1024) * 100) / 100,
      keys: allKeys,
    };
  },

  /**
   * Migra datos de una versión anterior (útil para cambios de prefijo)
   */
  migrate(oldPrefix: string): number {
    try {
      const keys = Object.keys(localStorage);
      const oldKeys = keys.filter((key) => key.startsWith(oldPrefix));

      let migrated = 0;
      oldKeys.forEach((oldKey) => {
        const value = localStorage.getItem(oldKey);
        if (value) {
          const newKey = oldKey.replace(oldPrefix, authConfig.storagePrefix);
          localStorage.setItem(newKey, value);
          localStorage.removeItem(oldKey);
          migrated++;
        }
      });

      logger.info(
        `Storage migrated: ${migrated} keys from ${oldPrefix} to ${authConfig.storagePrefix}`
      );
      return migrated;
    } catch (error) {
      logger.error('Error migrating storage:', error);
      return 0;
    }
  },

  /**
   * Guarda la preferencia de tema
   */
  setThemePreference(theme: 'light' | 'dark' | 'auto'): boolean {
    return this.setItem('theme', theme);
  },

  /**
   * Obtiene la preferencia de tema
   */
  getThemePreference(): 'light' | 'dark' | 'auto' | null {
    return this.getItem<'light' | 'dark' | 'auto'>('theme');
  },
};

/**
 * Servicio específico para tokens de autenticación
 */
export const authStorage = {
  /**
   * Guarda el token de acceso
   */
  setAccessToken(token: string): boolean {
    return storageService.setItem(authConfig.tokenKey, token);
  },

  /**
   * Obtiene el token de acceso
   */
  getAccessToken(): string | null {
    return storageService.getItem<string>(authConfig.tokenKey);
  },

  /**
   * Guarda el refresh token
   */
  setRefreshToken(token: string): boolean {
    return storageService.setItem(authConfig.refreshKey, token);
  },

  /**
   * Obtiene el refresh token
   */
  getRefreshToken(): string | null {
    return storageService.getItem<string>(authConfig.refreshKey);
  },

  /**
   * Guarda los datos del usuario
   */
  setUser(user: User): boolean {
    return storageService.setItem('user', user);
  },

  /**
   * Obtiene los datos del usuario
   */
  getUser(): User | null {
    return storageService.getItem<User>('user');
  },

  /**
   * Limpia todos los datos de autenticación
   */
  clearAuth(): void {
    const authKeys = [authConfig.tokenKey, authConfig.refreshKey, 'user'];
    authKeys.forEach((key) => {
      storageService.removeItem(key);
    });
  },

  /**
   * Verifica si el usuario está autenticado
   */
  isAuthenticated(): boolean {
    return !!(this.getAccessToken() && this.getUser());
  },
};

export default storageService;
