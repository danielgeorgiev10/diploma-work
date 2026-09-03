import apiClient from './apiClient';

const getErrorMessage = (error, fallback) =>
  error.response?.data?.detail || error.response?.data?.message || fallback;

export const userService = {
  async listUsers(search = null, skip = 0, limit = 25) {
    try {
      const params = { skip, limit };
      if (search) params.search = search;
      const response = await apiClient.get('/api/v1/users/', { params });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to load users'));
    }
  },

  async updateRole(userId, role) {
    try {
      const response = await apiClient.patch(`/api/v1/users/${userId}/role`, { role });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to update user role'));
    }
  },

  async updateStatus(userId, isActive) {
    try {
      const response = await apiClient.patch(`/api/v1/users/${userId}/status`, { is_active: isActive });
      return response.data;
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to update user status'));
    }
  },

  async deleteUser(userId) {
    try {
      await apiClient.delete(`/api/v1/users/${userId}`);
    } catch (error) {
      throw new Error(getErrorMessage(error, 'Failed to delete user'));
    }
  },
};
