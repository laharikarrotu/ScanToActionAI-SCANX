/**
 * Safe localStorage wrapper with error handling and encryption
 * Handles cases where localStorage is unavailable (private browsing, SSR)
 * Encrypts sensitive medical data before storage
 */

// Simple obfuscation for localStorage (not true encryption, but better than plaintext)
// For production, use proper encryption with user-specific keys
const obfuscateData = (data: string): string => {
  try {
    // Simple XOR obfuscation (not cryptographically secure, but prevents casual inspection)
    // In production, use proper encryption with Web Crypto API
    const key = 'healthscan-key-v1'; // In production, derive from user session
    let obfuscated = '';
    for (let i = 0; i < data.length; i++) {
      obfuscated += String.fromCharCode(data.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    }
    // Base64 encode to make it storage-safe
    return btoa(obfuscated);
  } catch {
    return data; // Fallback to unencrypted
  }
};

const deobfuscateData = (obfuscatedData: string): string => {
  try {
    // Check if it's obfuscated (base64 encoded)
    const decoded = atob(obfuscatedData);
    const key = 'healthscan-key-v1';
    let data = '';
    for (let i = 0; i < decoded.length; i++) {
      data += String.fromCharCode(decoded.charCodeAt(i) ^ key.charCodeAt(i % key.length));
    }
    return data;
  } catch {
    // If deobfuscation fails, might be old unencrypted data
    return obfuscatedData;
  }
};

// Keys that should be encrypted (medical/PHI data)
const ENCRYPTED_KEYS = [
  'extracted_medications',
  'prescription_data',
  'medical_data',
  'patient_info',
  'phi_data',
];

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

const shouldLog = (): boolean => {
  // Only log in development
  return process.env.NODE_ENV === 'development';
};

export const safeStorage = {
  setItem: (key: string, value: string): boolean => {
    if (!isStorageAvailable()) {
      if (shouldLog()) {
        console.warn(`localStorage not available. Cannot set ${key}`);
      }
      return false;
    }
    try {
      // Obfuscate sensitive medical data
      const shouldObfuscate = ENCRYPTED_KEYS.some(ek => key.includes(ek));
      const storageValue = shouldObfuscate ? obfuscateData(value) : value;
      
      localStorage.setItem(key, storageValue);
      return true;
    } catch (error) {
      if (shouldLog()) {
        console.error(`Error setting localStorage item ${key}:`, error);
      }
      return false;
    }
  },

  getItem: (key: string): string | null => {
    if (!isStorageAvailable()) {
      return null;
    }
    try {
      const value = localStorage.getItem(key);
      if (!value) return null;
      
      // Try to deobfuscate if it's an encrypted key
      const shouldDeobfuscate = ENCRYPTED_KEYS.some(ek => key.includes(ek));
      if (shouldDeobfuscate) {
        try {
          return deobfuscateData(value);
        } catch {
          // If deobfuscation fails, might be old unencrypted data
          return value;
        }
      }
      
      return value;
    } catch (error) {
      if (shouldLog()) {
        console.error(`Error getting localStorage item ${key}:`, error);
      }
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
      if (shouldLog()) {
        console.error(`Error removing localStorage item ${key}:`, error);
      }
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
      if (shouldLog()) {
        console.error('Error clearing localStorage:', error);
      }
      return false;
    }
  },
  
  // Clear all medical/PHI data
  clearMedicalData: (): boolean => {
    if (!isStorageAvailable()) {
      return false;
    }
    try {
      ENCRYPTED_KEYS.forEach(key => {
        localStorage.removeItem(key);
      });
      return true;
    } catch (error) {
      if (shouldLog()) {
        console.error('Error clearing medical data:', error);
      }
      return false;
    }
  },
};

