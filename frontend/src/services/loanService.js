import apiClient from './apiClient';

export const loanService = {
  async listLoans(userId = null, bookId = null, skip = 0, limit = 25) {
    try {
      const params = { skip, limit };
      if (userId) params.user_id = userId;
      if (bookId) params.book_id = bookId;
      
      const response = await apiClient.get('/api/v1/loans/', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getLoan(loanId) {
    try {
      const response = await apiClient.get(`/api/v1/loans/${loanId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async createLoan(userId, bookId, dueDate) {
    try {
      const response = await apiClient.post('/api/v1/loans/', {
        user_id: userId,
        book_id: bookId,
        due_date: dueDate,
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async returnLoan(loanId) {
    try {
      const response = await apiClient.post(`/api/v1/loans/${loanId}/return`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};
