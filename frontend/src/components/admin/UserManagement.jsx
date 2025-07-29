import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../services/admin';

const UserManagement = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false);

  const queryClient = useQueryClient();

  const { data: usersData, isLoading, error } = useQuery({
    queryKey: ['admin-users', currentPage, searchTerm, filterRole, filterStatus],
    queryFn: () => adminService.getUsers({
      page: currentPage,
      search: searchTerm,
      role: filterRole !== 'all' ? filterRole : undefined,
      status: filterStatus !== 'all' ? filterStatus : undefined,
    }),
  });

  const updateUserStatusMutation = useMutation({
    mutationFn: ({ userId, status }) => adminService.updateUserStatus(userId, status),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-users']);
      setShowUserModal(false);
    },
  });

  const suspendUserMutation = useMutation({
    mutationFn: ({ userId, reason }) => adminService.suspendUser(userId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries(['admin-users']);
      setShowUserModal(false);
    },
  });

  const handleUserAction = (user, action) => {
    setSelectedUser(user);
    if (action === 'view') {
      setShowUserModal(true);
    } else if (action === 'activate') {
      updateUserStatusMutation.mutate({ userId: user.id, status: 'active' });
    } else if (action === 'deactivate') {
      updateUserStatusMutation.mutate({ userId: user.id, status: 'inactive' });
    } else if (action === 'suspend') {
      const reason = prompt('Enter suspension reason:');
      if (reason) {
        suspendUserMutation.mutate({ userId: user.id, reason });
      }
    }
  };

  const UserModal = ({ user, onClose }) => (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>User Details</h3>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="user-details">
            <div className="detail-row">
              <label>Name:</label>
              <span>{user.first_name} {user.last_name}</span>
            </div>
            <div className="detail-row">
              <label>Email:</label>
              <span>{user.email}</span>
            </div>
            <div className="detail-row">
              <label>Phone:</label>
              <span>{user.phone || 'Not provided'}</span>
            </div>
            <div className="detail-row">
              <label>Role:</label>
              <span className={`role-badge role-${user.role}`}>{user.role}</span>
            </div>
            <div className="detail-row">
              <label>Status:</label>
              <span className={`status-badge status-${user.status}`}>{user.status}</span>
            </div>
            <div className="detail-row">
              <label>Verified:</label>
              <span>{user.is_verified ? '✅ Yes' : '❌ No'}</span>
            </div>
            <div className="detail-row">
              <label>Joined:</label>
              <span>{new Date(user.created_at).toLocaleDateString()}</span>
            </div>
            <div className="detail-row">
              <label>Last Active:</label>
              <span>{user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}</span>
            </div>
          </div>
          <div className="user-stats">
            <h4>User Statistics</h4>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-value">{user.total_bookings || 0}</span>
                <span className="stat-label">Total Bookings</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">${user.total_spent || 0}</span>
                <span className="stat-label">Total Spent</span>
              </div>
              <div className="stat-item">
                <span className="stat-value">{user.avg_rating || 'N/A'}</span>
                <span className="stat-label">Avg Rating</span>
              </div>
            </div>
          </div>
        </div>
        <div className="modal-actions">
          <button 
            className="btn btn-success"
            onClick={() => handleUserAction(user, 'activate')}
            disabled={user.status === 'active'}
          >
            Activate
          </button>
          <button 
            className="btn btn-warning"
            onClick={() => handleUserAction(user, 'deactivate')}
            disabled={user.status === 'inactive'}
          >
            Deactivate
          </button>
          <button 
            className="btn btn-danger"
            onClick={() => handleUserAction(user, 'suspend')}
          >
            Suspend
          </button>
        </div>
      </div>
    </div>
  );

  if (isLoading) {
    return <div className="loading">Loading users...</div>;
  }

  if (error) {
    return <div className="error">Error loading users: {error.message}</div>;
  }

  return (
    <div className="user-management">
      <div className="page-header">
        <h2>User Management</h2>
        <div className="header-actions">
          <button className="btn btn-primary">Export Users</button>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search users by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="filter-controls">
          <select value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
            <option value="all">All Roles</option>
            <option value="passenger">Passengers</option>
            <option value="driver">Drivers</option>
            <option value="admin">Admins</option>
          </select>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="users-table-container">
        <table className="users-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Verified</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {usersData?.users?.map((user) => (
              <tr key={user.id}>
                <td>{user.first_name} {user.last_name}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`role-badge role-${user.role}`}>
                    {user.role}
                  </span>
                </td>
                <td>
                  <span className={`status-badge status-${user.status}`}>
                    {user.status}
                  </span>
                </td>
                <td>{user.is_verified ? '✅' : '❌'}</td>
                <td>{new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                  <div className="action-buttons">
                    <button 
                      className="btn btn-sm btn-info"
                      onClick={() => handleUserAction(user, 'view')}
                    >
                      View
                    </button>
                    <button 
                      className="btn btn-sm btn-success"
                      onClick={() => handleUserAction(user, 'activate')}
                      disabled={user.status === 'active'}
                    >
                      Activate
                    </button>
                    <button 
                      className="btn btn-sm btn-danger"
                      onClick={() => handleUserAction(user, 'suspend')}
                    >
                      Suspend
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button 
          disabled={currentPage === 1}
          onClick={() => setCurrentPage(currentPage - 1)}
        >
          Previous
        </button>
        <span>Page {currentPage} of {usersData?.total_pages || 1}</span>
        <button 
          disabled={currentPage === usersData?.total_pages}
          onClick={() => setCurrentPage(currentPage + 1)}
        >
          Next
        </button>
      </div>

      {/* User Modal */}
      {showUserModal && selectedUser && (
        <UserModal 
          user={selectedUser} 
          onClose={() => setShowUserModal(false)} 
        />
      )}
    </div>
  );
};

export default UserManagement;