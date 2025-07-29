import React, { useState } from 'react';
import useNotifications from '../../hooks/useNotifications';

const NotificationCenter = ({ tripId, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [filter, setFilter] = useState('all'); // all, unread, high
  
  const {
    notifications,
    unreadCount,
    permission,
    requestPermission,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearAll
  } = useNotifications(tripId);

  // Filter notifications
  const filteredNotifications = notifications.filter(notification => {
    switch (filter) {
      case 'unread':
        return !notification.read;
      case 'high':
        return notification.priority === 'high';
      default:
        return true;
    }
  });

  // Get notification icon
  const getNotificationIcon = (type, priority) => {
    const icons = {
      status_update: priority === 'high' ? '🚨' : '📍',
      eta_update: '⏰',
      location_update: '🗺️',
      booking_update: '📋'
    };
    return icons[type] || '📢';
  };

  // Get notification color
  const getNotificationColor = (priority, read) => {
    if (read) return 'bg-gray-50 border-gray-200';
    
    switch (priority) {
      case 'high':
        return 'bg-red-50 border-red-200';
      case 'normal':
        return 'bg-blue-50 border-blue-200';
      default:
        return 'bg-gray-50 border-gray-300';
    }
  };

  // Format time
  const formatTime = (date) => {
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  return (
    <div className={`relative ${className}`}>
      {/* Notification Bell */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-lg"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM11 19H6.414a1 1 0 01-.707-.293L4 17V6a3 3 0 013-3h10a3 3 0 013 3v5" />
        </svg>
        
        {/* Unread badge */}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Notification Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          {/* Header */}
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Notifications</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Permission Request */}
            {permission !== 'granted' && (
              <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                <p className="text-sm text-yellow-800 mb-2">
                  Enable notifications to get real-time updates
                </p>
                <button
                  onClick={requestPermission}
                  className="text-xs bg-yellow-600 text-white px-2 py-1 rounded hover:bg-yellow-700"
                >
                  Enable Notifications
                </button>
              </div>
            )}

            {/* Filter Tabs */}
            <div className="flex space-x-1">
              {[
                { key: 'all', label: 'All' },
                { key: 'unread', label: `Unread (${unreadCount})` },
                { key: 'high', label: 'Important' }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key)}
                  className={`px-3 py-1 text-xs rounded ${
                    filter === tab.key
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-b border-gray-100 flex justify-between">
              <button
                onClick={markAllAsRead}
                className="text-xs text-blue-600 hover:text-blue-800"
                disabled={unreadCount === 0}
              >
                Mark all read
              </button>
              <button
                onClick={clearAll}
                className="text-xs text-red-600 hover:text-red-800"
              >
                Clear all
              </button>
            </div>
          )}

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {filteredNotifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                <div className="mb-2">📭</div>
                <p className="text-sm">
                  {filter === 'all' ? 'No notifications yet' : `No ${filter} notifications`}
                </p>
              </div>
            ) : (
              filteredNotifications.map(notification => (
                <div
                  key={notification.id}
                  className={`p-3 border-b border-gray-100 last:border-b-0 ${getNotificationColor(notification.priority, notification.read)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-1">
                        <span className="mr-2">
                          {getNotificationIcon(notification.type, notification.priority)}
                        </span>
                        <h4 className="text-sm font-medium text-gray-900">
                          {notification.title}
                        </h4>
                        {!notification.read && (
                          <div className="w-2 h-2 bg-blue-500 rounded-full ml-2"></div>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        {notification.message}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">
                          {formatTime(notification.timestamp)}
                        </span>
                        <div className="flex space-x-2">
                          {!notification.read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="text-xs text-blue-600 hover:text-blue-800"
                            >
                              Mark read
                            </button>
                          )}
                          <button
                            onClick={() => removeNotification(notification.id)}
                            className="text-xs text-red-600 hover:text-red-800"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Overlay to close panel */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default NotificationCenter;