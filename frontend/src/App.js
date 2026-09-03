import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import LoginPage from './pages/LoginPage';
import StudentDashboard from './pages/StudentDashboard';
import LibrarianDashboard from './pages/LibrarianDashboard';
import AdminDashboard from './pages/AdminDashboard';
import ProtectedRoute from './components/ProtectedRoute';
import { authService } from './services/authService';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('accessToken');
    if (token) {
      authService.getCurrentUser()
        .then(user => {
          setCurrentUser(user);
        })
        .catch(() => {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  };

  if (loading) {
    return <div className="loading-container">Loading...</div>;
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={
            currentUser ? <Navigate to="/" /> : <LoginPage onLogin={handleLogin} />
          } 
        />
        <Route 
          path="/" 
          element={
            currentUser ? (
              currentUser.role === 'student' ? <Navigate to="/student" /> :
              currentUser.role === 'librarian' ? <Navigate to="/librarian" /> :
              currentUser.role === 'admin' ? <Navigate to="/admin" /> :
              <Navigate to="/login" />
            ) : (
              <Navigate to="/login" />
            )
          }
        />
        <Route
          path="/student/*"
          element={
            <ProtectedRoute user={currentUser} allowedRoles={['student']}>
              <StudentDashboard user={currentUser} onLogout={handleLogout} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/librarian/*"
          element={
            <ProtectedRoute user={currentUser} allowedRoles={['librarian', 'admin']}>
              <LibrarianDashboard user={currentUser} onLogout={handleLogout} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/*"
          element={
            <ProtectedRoute user={currentUser} allowedRoles={['admin']}>
              <AdminDashboard user={currentUser} onLogout={handleLogout} />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
