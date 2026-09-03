import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { bookService } from '../services/bookService';
import { loanService } from '../services/loanService';
import './StudentDashboard.css';

const StudentDashboard = ({ user, onLogout }) => {
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
                to="/student/books" 
                className={location.pathname === '/student/books' ? 'active' : ''}
              >
                📖 Browse Books
              </Link>
            </li>
            <li>
              <Link 
                to="/student/loans" 
                className={location.pathname === '/student/loans' ? 'active' : ''}
              >
                📋 My Loans
              </Link>
            </li>
          </nav>
        </aside>

        <main className="content-area">
          <Routes>
            <Route path="/books" element={<BooksPage userId={user.id} />} />
            <Route path="/loans" element={<LoansPage userId={user.id} />} />
            <Route path="/" element={<BooksPage userId={user.id} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const BooksPage = ({ userId }) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchAuthor, setSearchAuthor] = useState('');
  const [searchTitle, setSearchTitle] = useState('');
  const [borrowLoading, setBorrowLoading] = useState({});
  const [borrowSuccess, setBorrowSuccess] = useState('');

  useEffect(() => {
    const loadInitialBooks = async () => {
      try {
        setLoading(true);
        setError('');
        const data = await bookService.listBooks(null, null);
        setBooks(data);
      } catch (err) {
        setError(err.detail || 'Failed to load books');
      } finally {
        setLoading(false);
      }
    };

    loadInitialBooks();
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

  const handleBorrow = async (bookId, bookTitle) => {
    setBorrowLoading(prev => ({ ...prev, [bookId]: true }));
    try {
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + 14);
      
      await loanService.createLoan(userId, bookId, dueDate.toISOString());
      setBorrowSuccess(`Successfully borrowed "${bookTitle}"`);
      setTimeout(() => setBorrowSuccess(''), 3000);
      
      loadBooks();
    } catch (err) {
      setError(err.detail || 'Failed to borrow book');
    } finally {
      setBorrowLoading(prev => ({ ...prev, [bookId]: false }));
    }
  };

  return (
    <div className="books-page">
      <div className="card">
        <h2 className="card-title">Search Books</h2>
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
        </form>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {borrowSuccess && <div className="alert alert-success">{borrowSuccess}</div>}

      <div className="card">
        <h2 className="card-title">Available Books</h2>
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
                  <th>Available</th>
                  <th>Action</th>
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
                        {book.copies_available} copies
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-success"
                        onClick={() => handleBorrow(book.id, book.title)}
                        disabled={book.copies_available === 0 || borrowLoading[book.id]}
                      >
                        {borrowLoading[book.id] ? 'Borrowing...' : 'Borrow'}
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

const LoansPage = ({ userId }) => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [returnLoading, setReturnLoading] = useState({});
  const [returnSuccess, setReturnSuccess] = useState('');

  useEffect(() => {
    const loadInitialLoans = async () => {
      try {
        setLoading(true);
        setError('');
        const data = await loanService.listLoans(userId);
        setLoans(data);
      } catch (err) {
        setError(err.detail || 'Failed to load loans');
      } finally {
        setLoading(false);
      }
    };

    loadInitialLoans();
  }, []);

  const loadLoans = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await loanService.listLoans(userId);
      setLoans(data);
    } catch (err) {
      setError(err.detail || 'Failed to load loans');
    } finally {
      setLoading(false);
    }
  };

  const handleReturn = async (loanId) => {
    setReturnLoading(prev => ({ ...prev, [loanId]: true }));
    try {
      await loanService.returnLoan(loanId);
      setReturnSuccess('Book returned successfully');
      setTimeout(() => setReturnSuccess(''), 3000);
      loadLoans();
    } catch (err) {
      setError(err.detail || 'Failed to return book');
    } finally {
      setReturnLoading(prev => ({ ...prev, [loanId]: false }));
    }
  };

  return (
    <div className="loans-page">
      {error && <div className="alert alert-error">{error}</div>}
      {returnSuccess && <div className="alert alert-success">{returnSuccess}</div>}

      <div className="card">
        <h2 className="card-title">My Loans</h2>
        {loading ? (
          <div className="spinner"></div>
        ) : loans.length === 0 ? (
          <p>You don't have any loans.</p>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Book</th>
                  <th>Borrowed</th>
                  <th>Due Date</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {loans.map(loan => {
                  const dueDate = new Date(loan.due_date);
                  const isOverdue = !loan.returned && dueDate < new Date();
                  
                  return (
                    <tr key={loan.id}>
                      <td>Book #{loan.book_id}</td>
                      <td>{new Date(loan.loan_date).toLocaleDateString()}</td>
                      <td>{dueDate.toLocaleDateString()}</td>
                      <td>
                        <span className={`badge ${loan.returned ? 'badge-info' : isOverdue ? 'badge-danger' : 'badge-success'}`}>
                          {loan.returned ? 'Returned' : isOverdue ? 'Overdue' : 'Active'}
                        </span>
                      </td>
                      <td>
                        {!loan.returned && (
                          <button
                            className="btn btn-primary"
                            onClick={() => handleReturn(loan.id)}
                            disabled={returnLoading[loan.id]}
                          >
                            {returnLoading[loan.id] ? 'Returning...' : 'Return'}
                          </button>
                        )}
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

export default StudentDashboard;
