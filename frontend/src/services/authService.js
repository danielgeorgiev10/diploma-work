import apiClient from './apiClient';

export const authService = {
  async register(email, password, fullName) {
    try {
      const response = await apiClient.post('/api/v1/auth/register', {
        email,
        password,
        full_name: fullName,
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async login(email, password) {
    try {
      const response = await apiClient.post('/api/v1/auth/login', {
        email,
        password,
      });
      
      const { access_token, refresh_token } = response.data;
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getCurrentUser() {
    try {
      const response = await apiClient.get('/api/v1/auth/me');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  logout() {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
};
