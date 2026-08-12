import { describe, it, expect, beforeEach } from 'vitest';
import { storageService } from '../../services/storage';

describe('Storage Service', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('stores and retrieves items', () => {
    const testData = { name: 'test', value: 123 };
    storageService.setItem('test-key', testData);

    const retrieved = storageService.getItem('test-key');
    expect(retrieved).toEqual(testData);
  });

  it('returns null for non-existent keys', () => {
    const result = storageService.getItem('non-existent');
    expect(result).toBeNull();
  });

  it('removes items correctly', () => {
    storageService.setItem('remove-me', 'data');
    storageService.removeItem('remove-me');

    const result = storageService.getItem('remove-me');
    expect(result).toBeNull();
  });

  it('clears all items', () => {
    storageService.setItem('key1', 'value1');
    storageService.setItem('key2', 'value2');
    storageService.clear();

    expect(storageService.getItem('key1')).toBeNull();
    expect(storageService.getItem('key2')).toBeNull();
  });
});
