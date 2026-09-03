import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { bookService } from '../services/bookService';
import { loanService } from '../services/loanService';
import './LibrarianDashboard.css';

const LibrarianDashboard = ({ user, onLogout }) => {
  const location = useLocation();

  return (
    <div className="dashboard">
      <header className="header">
        <div className="header-top">
          <h1 className="header-title">📚 Library Management</h1>
          <div className="user-info">
            <span>{user.full_name}</span>
            <span className="user-role">{user.role}</span>
            <button className="logout-btn" onClick={onLogout}>Logout</button>
          </div>
        </div>
      </header>

      <div className="dashboard-container">
        <aside className="sidebar">
          <nav className="sidebar-nav">
            <li>
              <Link 
                to="/librarian/books" 
                className={location.pathname === '/librarian/books' ? 'active' : ''}
              >
                📖 Manage Books
              </Link>
            </li>
            <li>
              <Link 
                to="/librarian/loans" 
                className={location.pathname === '/librarian/loans' ? 'active' : ''}
              >
                📋 View Loans
              </Link>
            </li>
          </nav>
        </aside>

        <main className="content-area">
          <Routes>
            <Route path="/books" element={<BooksManagementPage />} />
            <Route path="/loans" element={<LoansViewPage />} />
            <Route path="/" element={<BooksManagementPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const BooksManagementPage = () => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchAuthor, setSearchAuthor] = useState('');
  const [searchTitle, setSearchTitle] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    author: '',
    isbn: '',
    published_year: '',
    copies_available: '1',
  });

  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await bookService.listBooks(
        searchAuthor || null,
        searchTitle || null
      );
      setBooks(data);
    } catch (err) {
      setError(err.detail || 'Failed to load books');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    loadBooks();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCreateBook = async (e) => {
    e.preventDefault();
    try {
      setError('');
      await bookService.createBook(
        formData.title,
        formData.author,
        formData.isbn,
        formData.published_year ? parseInt(formData.published_year) : null,
        parseInt(formData.copies_available)
      );
      setSuccessMessage('Book created successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      setShowCreateForm(false);
      setFormData({
        title: '',
        author: '',
        isbn: '',
        published_year: '',
        copies_available: '1',
      });
      loadBooks();
    } catch (err) {
      setError(err.detail || 'Failed to create book');
    }
  };

  const handleUpdateBook = async (e) => {
    e.preventDefault();
    try {
      setError('');
      const updates = {};
      if (formData.title) updates.title = formData.title;
      if (formData.author) updates.author = formData.author;
      if (formData.isbn) updates.isbn = formData.isbn;
      if (formData.published_year) updates.published_year = parseInt(formData.published_year);

      await bookService.updateBook(editingId, updates);
      setSuccessMessage('Book updated successfully');
      setTimeout(() => setSuccessMessage(''), 3000);
      setEditingId(null);
      setFormData({
        title: '',
        author: '',
        isbn: '',
        published_year: '',
        copies_available: '1',
      });
      loadBooks();
    } catch (err) {
      setError(err.detail || 'Failed to update book');
    }
  };

  const handleDeleteBook = async (bookId) => {
    if (window.confirm('Are you sure you want to delete this book?')) {
      try {
        setError('');
        await bookService.deleteBook(bookId);
        setSuccessMessage('Book deleted successfully');
        setTimeout(() => setSuccessMessage(''), 3000);
        loadBooks();
      } catch (err) {
        setError(err.detail || 'Failed to delete book');
      }
    }
  };

  const startEdit = (book) => {
    setEditingId(book.id);
    setFormData({
      title: book.title,
      author: book.author,
      isbn: book.isbn,
      published_year: book.published_year || '',
      copies_available: book.copies_available.toString(),
    });
    setShowCreateForm(false);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setShowCreateForm(false);
    setFormData({
      title: '',
      author: '',
      isbn: '',
      published_year: '',
      copies_available: '1',
    });
  };

  return (
    <div className="books-management-page">
      <div className="card">
        <h2 className="card-title">Search & Filter Books</h2>
        <form onSubmit={handleSearch}>
          <div className="form-row">
            <div className="form-group">
              <label>Author</label>
              <input
                type="text"
                value={searchAuthor}
                onChange={(e) => setSearchAuthor(e.target.value)}
                placeholder="Search by author..."
              />
            </div>
            <div className="form-group">
              <label>Title</label>
              <input
                type="text"
                value={searchTitle}
                onChange={(e) => setSearchTitle(e.target.value)}
                placeholder="Search by title..."
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary">Search</button>
          <button 
            type="button" 
            className="btn btn-success" 
            onClick={() => {
              setShowCreateForm(!showCreateForm);
              setEditingId(null);
              setFormData({
                title: '',
                author: '',
                isbn: '',
                published_year: '',
                copies_available: '1',
              });
            }}
          >
            {showCreateForm ? 'Cancel' : '+ Add New Book'}
          </button>
        </form>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {successMessage && <div className="alert alert-success">{successMessage}</div>}

      {(showCreateForm || editingId) && (
        <div className="card">
          <h2 className="card-title">{editingId ? 'Edit Book' : 'Create New Book'}</h2>
          <form onSubmit={editingId ? handleUpdateBook : handleCreateBook}>
            <div className="form-row">
              <div className="form-group">
                <label>Title *</label>
                <input
                  type="text"
                  name="title"
                  value={formData.title}
                  onChange={handleInputChange}
                  placeholder="Book title"
                  required={!editingId}
                />
              </div>
              <div className="form-group">
                <label>Author *</label>
                <input
                  type="text"
                  name="author"
                  value={formData.author}
                  onChange={handleInputChange}
                  placeholder="Author name"
                  required={!editingId}
                />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>ISBN *</label>
                <input
                  type="text"
                  name="isbn"
                  value={formData.isbn}
                  onChange={handleInputChange}
                  placeholder="ISBN (10-20 chars)"
                  required={!editingId}
                />
              </div>
              <div className="form-group">
                <label>Published Year</label>
                <input
                  type="number"
                  name="published_year"
                  value={formData.published_year}
                  onChange={handleInputChange}
                  placeholder="e.g., 2023"
                />
              </div>
            </div>
            <div className="form-group">
              <label>Available Copies *</label>
              <input
                type="number"
                name="copies_available"
                value={formData.copies_available}
                onChange={handleInputChange}
                min="0"
                required={!editingId}
              />
            </div>
            <div className="btn-group">
              <button type="submit" className="btn btn-success">
                {editingId ? 'Update Book' : 'Create Book'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={cancelEdit}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <h2 className="card-title">Book Catalog</h2>
        {loading ? (
          <div className="spinner"></div>
        ) : books.length === 0 ? (
          <p>No books found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Author</th>
                  <th>ISBN</th>
                  <th>Year</th>
                  <th>Copies</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {books.map(book => (
                  <tr key={book.id}>
                    <td>{book.title}</td>
                    <td>{book.author}</td>
                    <td>{book.isbn}</td>
                    <td>{book.published_year || '-'}</td>
                    <td>
                      <span className={`badge ${book.copies_available > 0 ? 'badge-success' : 'badge-danger'}`}>
                        {book.copies_available}
                      </span>
                    </td>
                    <td>
                      <button 
                        className="btn btn-primary" 
                        onClick={() => startEdit(book)}
                      >
                        Edit
                      </button>
                      <button 
                        className="btn btn-danger" 
                        onClick={() => handleDeleteBook(book.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

const LoansViewPage = () => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadLoans();
  }, []);

  const loadLoans = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await loanService.listLoans();
      setLoans(data);
    } catch (err) {
      setError(err.detail || 'Failed to load loans');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="loans-view-page">
      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2 className="card-title">All Loans</h2>
        {loading ? (
          <div className="spinner"></div>
        ) : loans.length === 0 ? (
          <p>No loans found.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>User ID</th>
                  <th>Book ID</th>
                  <th>Borrowed</th>
                  <th>Due Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {loans.map(loan => {
                  const dueDate = new Date(loan.due_date);
                  const isOverdue = !loan.returned && dueDate < new Date();
                  
                  return (
                    <tr key={loan.id}>
                      <td>{loan.user_id}</td>
                      <td>{loan.book_id}</td>
                      <td>{new Date(loan.loan_date).toLocaleDateString()}</td>
                      <td>{dueDate.toLocaleDateString()}</td>
                      <td>
                        <span className={`badge ${loan.returned ? 'badge-info' : isOverdue ? 'badge-danger' : 'badge-success'}`}>
                          {loan.returned ? 'Returned' : isOverdue ? 'Overdue' : 'Active'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export { BooksManagementPage, LoansViewPage };
export default LibrarianDashboard;
