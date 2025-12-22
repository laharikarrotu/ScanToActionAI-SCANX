/**
 * Safe localStorage wrapper with error handling
 * Handles cases where localStorage is unavailable (private browsing, SSR)
 */

const isStorageAvailable = (): boolean => {
  if (typeof window === 'undefined') return false;
  try {
    const test = '__storage_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
};

export const safeStorage = {
  setItem: (key: string, value: string): boolean => {
    if (!isStorageAvailable()) {
      console.warn(`localStorage not available. Cannot set ${key}`);
      return false;
    }
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      console.error(`Error setting localStorage item ${key}:`, error);
      return false;
    }
  },

  getItem: (key: string): string | null => {
    if (!isStorageAvailable()) {
      return null;
    }
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.error(`Error getting localStorage item ${key}:`, error);
      return null;
    }
  },

  removeItem: (key: string): boolean => {
    if (!isStorageAvailable()) {
      return false;
    }
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error(`Error removing localStorage item ${key}:`, error);
      return false;
    }
  },

  clear: (): boolean => {
    if (!isStorageAvailable()) {
      return false;
    }
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('Error clearing localStorage:', error);
      return false;
    }
  },
};

