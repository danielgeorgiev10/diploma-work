import apiClient from './apiClient';

export const bookService = {
  async listBooks(author = null, title = null, skip = 0, limit = 25) {
    try {
      const params = { skip, limit };
      if (author) params.author = author;
      if (title) params.title = title;
      
      const response = await apiClient.get('/api/v1/books/', { params });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async getBook(bookId) {
    try {
      const response = await apiClient.get(`/api/v1/books/${bookId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async createBook(title, author, isbn, publishedYear, copiesAvailable) {
    try {
      const response = await apiClient.post('/api/v1/books/', {
        title,
        author,
        isbn,
        published_year: publishedYear,
        copies_available: copiesAvailable,
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async updateBook(bookId, updates) {
    try {
      const response = await apiClient.put(`/api/v1/books/${bookId}`, updates);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  async deleteBook(bookId) {
    try {
      const response = await apiClient.delete(`/api/v1/books/${bookId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};
