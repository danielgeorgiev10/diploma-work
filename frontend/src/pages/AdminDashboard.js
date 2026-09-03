import React from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import './AdminDashboard.css';
import AdminUsersPage from './AdminUsersPage';
import { BooksManagementPage, LoansViewPage } from './LibrarianDashboard';

const AdminDashboard = ({ user, onLogout }) => {
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
                to="/admin/overview" 
                className={location.pathname === '/admin/overview' ? 'active' : ''}
              >
                📊 Overview
              </Link>
            </li>
            <li>
              <Link 
                to="/admin/users" 
                className={location.pathname === '/admin/users' ? 'active' : ''}
              >
                👥 Users
              </Link>
            </li>
            <li>
              <Link 
                to="/admin/books" 
                className={location.pathname === '/admin/books' ? 'active' : ''}
              >
                📖 Books
              </Link>
            </li>
            <li>
              <Link 
                to="/admin/loans" 
                className={location.pathname === '/admin/loans' ? 'active' : ''}
              >
                📋 Loans
              </Link>
            </li>
          </nav>
        </aside>

        <main className="content-area">
          <Routes>
            <Route path="/overview" element={<AdminOverviewPage />} />
            <Route path="/users" element={<AdminUsersPage />} />
            <Route path="/books" element={<BooksManagementPage />} />
            <Route path="/loans" element={<LoansViewPage />} />
            <Route path="/" element={<AdminOverviewPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

const AdminOverviewPage = () => {
  return (
    <div className="admin-overview">
      <div className="card">
        <h2 className="card-title">Admin Dashboard</h2>
        <p>Manage users, books, inventory, and loans from the administration workspace.</p>
      </div>

      <div className="card">
        <h2 className="card-title">Current System Capabilities</h2>
        <ul>
          <li>✅ User Authentication with JWT tokens</li>
          <li>✅ Role-based access control (admin, librarian, student)</li>
          <li>✅ Book catalog management (create, read, update, delete)</li>
          <li>✅ Book inventory tracking</li>
          <li>✅ Loan management (create, return)</li>
          <li>✅ User borrowing system with due dates</li>
          <li>✅ Admin-only user role and account status management</li>
          <li>✅ Safe deletion protection for users with loan history</li>
        </ul>
      </div>

      <div className="card">
        <h2 className="card-title">Available Endpoints by Role</h2>
        <div className="endpoints-grid">
          <div className="endpoint-section">
            <h3>Authentication (All Users)</h3>
            <ul>
              <li>POST /api/v1/auth/register</li>
              <li>POST /api/v1/auth/login</li>
              <li>GET /api/v1/auth/me</li>
            </ul>
          </div>

          <div className="endpoint-section">
            <h3>Books (Public Read, Librarian/Admin Write)</h3>
            <ul>
              <li>GET /api/v1/books/</li>
              <li>GET /api/v1/books/{'{book_id}'}</li>
              <li>POST /api/v1/books/ (librarian, admin)</li>
              <li>PATCH /api/v1/books/{'{book_id}'} (librarian, admin)</li>
              <li>DELETE /api/v1/books/{'{book_id}'} (librarian, admin)</li>
            </ul>
          </div>

          <div className="endpoint-section">
            <h3>Loans (Authenticated Users)</h3>
            <ul>
              <li>GET /api/v1/loans/</li>
              <li>GET /api/v1/loans/{'{loan_id}'}</li>
              <li>POST /api/v1/loans/ (create)</li>
              <li>POST /api/v1/loans/{'{loan_id}'}/return</li>
            </ul>
          </div>

          <div className="endpoint-section">
            <h3>Internal Service Endpoints</h3>
            <ul>
              <li>GET /api/v1/users/{'{user_id}'} (requires X-Internal-Service-Token)</li>
              <li>PATCH /api/v1/books/{'{book_id}'}/inventory/decrement (internal)</li>
              <li>PATCH /api/v1/books/{'{book_id}'}/inventory/increment (internal)</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Admin Functions Available</h2>
        <p>As an admin user, you can:</p>
        <ul>
          <li>✅ Access librarian features (book management, view loans)</li>
          <li>✅ Access all book catalog features</li>
          <li>✅ Manage book inventory</li>
          <li>✅ View all loans in the system</li>
        </ul>
      </div>

    </div>
  );
};

export default AdminDashboard;
