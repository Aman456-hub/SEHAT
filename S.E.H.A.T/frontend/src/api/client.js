import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token to all API requests
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('sehat_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiry / unauthenticated errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('sehat_token');
      localStorage.removeItem('sehat_role');
      localStorage.removeItem('sehat_user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

/**
 * Custom wrapper around Axios to interact with the backend API.
 * Ensures all responses are mapped to the strict { success, data, message, error } structure
 * and handles failures gracefully to prevent frontend crashes.
 */
export const api = {
  get: async (url, config = {}) => {
    try {
      const response = await client.get(url, config);
      return response.data;
    } catch (error) {
      return {
        success: false,
        data: null,
        message: error.response?.data?.detail || 'An error occurred while fetching data.',
        error: error.message,
      };
    }
  },
  
  post: async (url, data = {}, config = {}) => {
    try {
      const response = await client.post(url, data, config);
      return response.data;
    } catch (error) {
      return {
        success: false,
        data: null,
        message: error.response?.data?.detail || 'An error occurred while sending data.',
        error: error.message,
      };
    }
  },
  
  patch: async (url, data = {}, config = {}) => {
    try {
      const response = await client.patch(url, data, config);
      return response.data;
    } catch (error) {
      return {
        success: false,
        data: null,
        message: error.response?.data?.detail || 'An error occurred while updating data.',
        error: error.message,
      };
    }
  },
};

export default client;
