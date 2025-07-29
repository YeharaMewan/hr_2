// frontend/lib/config.js - Environment configuration
const getApiBaseUrl = () => {
  // Check if we're in browser environment
  if (typeof window !== 'undefined') {
    // Production: Use same origin as frontend
    if (window.location.hostname !== 'localhost') {
      return window.location.origin;
    }
    // Development: Use localhost with backend port
    return 'http://localhost:5000';
  }
  
  // Server-side rendering fallback
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
};