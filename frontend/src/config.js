// Dynamic config for API base URL in local/production builds
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
