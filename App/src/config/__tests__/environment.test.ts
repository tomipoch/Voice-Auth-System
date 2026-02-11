import { describe, it, expect } from 'vitest';
import { appConfig, authConfig, features, logger } from '../environment';

describe('environment configuration', () => {
  describe('appConfig', () => {
    it('has required properties', () => {
      expect(appConfig).toHaveProperty('name');
      expect(appConfig).toHaveProperty('version');
      expect(appConfig).toHaveProperty('environment');
    });

    it('has valid environment value', () => {
      expect(['development', 'production', 'test', 'staging']).toContain(appConfig.environment);
    });
  });

  describe('authConfig', () => {
    it('has token configuration', () => {
      expect(authConfig).toHaveProperty('tokenKey');
      expect(authConfig).toHaveProperty('refreshKey');
      expect(authConfig).toHaveProperty('storagePrefix');
    });

    it('has timeout values', () => {
      expect(authConfig).toHaveProperty('sessionTimeout');
      expect(typeof authConfig.sessionTimeout).toBe('number');
    });
  });

  describe('features', () => {
    it('has feature flags', () => {
      expect(features).toHaveProperty('consoleLogs');
      expect(features).toHaveProperty('debugMode');
    });

    it('feature flags are boolean', () => {
      expect(typeof features.consoleLogs).toBe('boolean');
      expect(typeof features.debugMode).toBe('boolean');
    });
  });

  describe('logger', () => {
    it('has logging methods', () => {
      expect(logger).toHaveProperty('info');
      expect(logger).toHaveProperty('warn');
      expect(logger).toHaveProperty('error');
      expect(logger).toHaveProperty('debug');
    });

    it('logging methods are functions', () => {
      expect(typeof logger.info).toBe('function');
      expect(typeof logger.warn).toBe('function');
      expect(typeof logger.error).toBe('function');
      expect(typeof logger.debug).toBe('function');
    });

    it('can call logger methods without errors', () => {
      expect(() => logger.info('test')).not.toThrow();
      expect(() => logger.warn('test')).not.toThrow();
      expect(() => logger.error('test')).not.toThrow();
      expect(() => logger.debug('test')).not.toThrow();
    });
  });
});
