import React, { useEffect, useState } from 'react';
import { userService } from '../services/userService';

const roles = ['student', 'librarian', 'admin'];

const getErrorMessage = (error, fallback) => error.message || fallback;

const AdminUsersPage = () => {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadUsers = async (query = search) => {
    try {
      setLoading(true);
      setError('');
      setUsers(await userService.listUsers(query.trim() || null));
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load users'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers('');
  }, []);

  const showSuccess = (message) => {
    setSuccess(message);
    window.setTimeout(() => setSuccess(''), 3000);
  };

  const handleRoleChange = async (userId, role) => {
    try {
      setError('');
      await userService.updateRole(userId, role);
      showSuccess('User role updated successfully');
      await loadUsers();
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to update user role'));
    }
  };

  const handleStatusChange = async (user) => {
    const action = user.is_active ? 'deactivate' : 'reactivate';
    if (!window.confirm(`Are you sure you want to ${action} ${user.email}?`)) return;

    try {
      setError('');
      await userService.updateStatus(user.id, !user.is_active);
      showSuccess(`User ${action}d successfully`);
      await loadUsers();
    } catch (err) {
      setError(getErrorMessage(err, `Failed to ${action} user`));
    }
  };

  const handleDelete = async (user) => {
    if (!window.confirm(`Delete ${user.email}? Users with loan history cannot be deleted.`)) return;

    try {
      setError('');
      await userService.deleteUser(user.id);
      showSuccess('User deleted successfully');
      await loadUsers();
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to delete user'));
    }
  };

  return (
    <div className="admin-users-page">
      <div className="card">
        <h2 className="card-title">Users</h2>
        <form onSubmit={(event) => { event.preventDefault(); loadUsers(); }}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="user-search">Search by name or email</label>
              <input
                id="user-search"
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search users..."
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary">Search</button>
        </form>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="card">
        {loading ? <div className="loading-container">Loading users...</div> : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Full name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>{user.id}</td>
                    <td>{user.full_name || '-'}</td>
                    <td>{user.email}</td>
                    <td>
                      <select value={user.role} onChange={(event) => handleRoleChange(user.id, event.target.value)}>
                        {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                      </select>
                    </td>
                    <td>
                      <span className={`badge ${user.is_active ? 'badge-success' : 'badge-danger'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div className="btn-group">
                        <button type="button" className="btn btn-secondary" onClick={() => handleStatusChange(user)}>
                          {user.is_active ? 'Deactivate' : 'Reactivate'}
                        </button>
                        <button type="button" className="btn btn-danger" onClick={() => handleDelete(user)}>
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {!users.length && <tr><td colSpan="6">No users found.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminUsersPage;
