import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/authService';
import './LoginPage.css';

const LoginPage = ({ onLogin }) => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);
  const [fullName, setFullName] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(email, password);
      const user = await authService.getCurrentUser();
      onLogin(user);
      navigate('/');
    } catch (err) {
      setError(err.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.register(email, password, fullName);
      // After registration, log in automatically
      await authService.login(email, password);
      const user = await authService.getCurrentUser();
      onLogin(user);
      navigate('/');
    } catch (err) {
      setError(err.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1 className="login-title">Library Management Platform</h1>
        
        {error && <div className="alert alert-error">{error}</div>}
        
        <form onSubmit={isRegister ? handleRegister : handleLogin}>
          {isRegister && (
            <div className="form-group">
              <label>Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
                required
                disabled={loading}
              />
            </div>
          )}

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary login-btn"
            disabled={loading}
          >
            {loading ? 'Loading...' : isRegister ? 'Register' : 'Login'}
          </button>
        </form>

        <div className="toggle-auth">
          {isRegister ? (
            <>
              Already have an account?{' '}
              <button
                onClick={() => {
                  setIsRegister(false);
                  setError('');
                  setFullName('');
                }}
                className="toggle-btn"
              >
                Login
              </button>
            </>
          ) : (
            <>
              Don't have an account?{' '}
              <button
                onClick={() => {
                  setIsRegister(true);
                  setError('');
                }}
                className="toggle-btn"
              >
                Register
              </button>
            </>
          )}
        </div>

        <div className="demo-info">
          <p className="demo-title">Demo Credentials:</p>
          <p><strong>Student:</strong> student@example.com / pass123</p>
          <p><strong>Librarian:</strong> librarian@example.com / pass123</p>
          <p><strong>Admin:</strong> admin@example.com / pass123</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
