import { useState, useEffect, useCallback } from 'react';
import useWebSocket from './useWebSocket';

export const useNotifications = (tripId = null) => {
  const [notifications, setNotifications] = useState([]);
  const [permission, setPermission] = useState(Notification.permission);
  const { subscribe, isConnected } = useWebSocket(tripId);

  // Request notification permission
  const requestPermission = useCallback(async () => {
    if ('Notification' in window) {
      const result = await Notification.requestPermission();
      setPermission(result);
      return result === 'granted';
    }
    return false;
  }, []);

  // Add notification to state
  const addNotification = useCallback((notification) => {
    const id = Date.now() + Math.random();
    const newNotification = {
      id,
      timestamp: new Date(),
      read: false,
      ...notification
    };

    setNotifications(prev => [newNotification, ...prev.slice(0, 49)]); // Keep last 50
    return id;
  }, []);

  // Remove notification
  const removeNotification = useCallback((id) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // Mark notification as read
  const markAsRead = useCallback((id) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  }, []);

  // Mark all as read
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  // Clear all notifications
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Show browser notification
  const showBrowserNotification = useCallback((title, options = {}) => {
    if (permission === 'granted' && 'Notification' in window) {
      const notification = new Notification(title, {
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        ...options
      });

      // Auto close after 5 seconds
      setTimeout(() => notification.close(), 5000);

      return notification;
    }
    return null;
  }, [permission]);

  // Handle different types of notifications
  const handleTripStatusUpdate = useCallback((data) => {
    const statusMessages = {
      boarding: 'Your bus is now boarding passengers',
      departed: 'Your bus has departed from the terminal',
      in_transit: 'Your bus is now on the way',
      approaching: 'Your bus is approaching the destination',
      arrived: 'Your bus has arrived at the destination',
      delayed: `Your trip is delayed by ${data.delay_minutes || 'unknown'} minutes`,
      cancelled: 'Your trip has been cancelled'
    };

    const message = statusMessages[data.status] || `Trip status updated to ${data.status}`;
    
    const notification = {
      type: 'status_update',
      title: 'Trip Status Update',
      message,
      tripId: data.trip_id,
      status: data.status,
      priority: ['cancelled', 'delayed'].includes(data.status) ? 'high' : 'normal'
    };

    addNotification(notification);

    // Show browser notification for important updates
    if (['boarding', 'departed', 'approaching', 'arrived', 'delayed', 'cancelled'].includes(data.status)) {
      showBrowserNotification('Trip Update', {
        body: message,
        tag: `trip-${data.trip_id}`,
        requireInteraction: ['cancelled', 'delayed'].includes(data.status)
      });
    }
  }, [addNotification, showBrowserNotification]);

  const handleETAUpdate = useCallback((data) => {
    const notification = {
      type: 'eta_update',
      title: 'ETA Updated',
      message: `New estimated arrival: ${new Date(data.eta_data.estimated_arrival).toLocaleTimeString()}`,
      tripId: data.trip_id,
      eta: data.eta_data,
      priority: 'low'
    };

    addNotification(notification);
  }, [addNotification]);

  const handleLocationUpdate = useCallback((data) => {
    // Only add location notifications for significant updates
    if (data.milestone) {
      const notification = {
        type: 'location_update',
        title: 'Location Update',
        message: data.milestone,
        tripId: data.trip_id,
        location: data.location,
        priority: 'low'
      };

      addNotification(notification);
    }
  }, [addNotification]);

  const handleBookingUpdate = useCallback((data) => {
    const notification = {
      type: 'booking_update',
      title: 'Booking Update',
      message: data.message || 'Your booking has been updated',
      bookingId: data.booking_id,
      priority: 'normal'
    };

    addNotification(notification);

    showBrowserNotification('Booking Update', {
      body: notification.message,
      tag: `booking-${data.booking_id}`
    });
  }, [addNotification, showBrowserNotification]);

  // Subscribe to WebSocket events
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribers = [
      subscribe('trip_status_update', handleTripStatusUpdate),
      subscribe('eta_update', handleETAUpdate),
      subscribe('location_update', handleLocationUpdate),
      subscribe('booking_update', handleBookingUpdate)
    ];

    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [
    isConnected,
    subscribe,
    handleTripStatusUpdate,
    handleETAUpdate,
    handleLocationUpdate,
    handleBookingUpdate
  ]);

  // Request permission on mount if not already granted
  useEffect(() => {
    if (permission === 'default') {
      requestPermission();
    }
  }, [permission, requestPermission]);

  // Get unread count
  const unreadCount = notifications.filter(n => !n.read).length;

  // Get notifications by type
  const getNotificationsByType = useCallback((type) => {
    return notifications.filter(n => n.type === type);
  }, [notifications]);

  // Get notifications by priority
  const getNotificationsByPriority = useCallback((priority) => {
    return notifications.filter(n => n.priority === priority);
  }, [notifications]);

  return {
    notifications,
    unreadCount,
    permission,
    requestPermission,
    addNotification,
    removeNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    showBrowserNotification,
    getNotificationsByType,
    getNotificationsByPriority
  };
};

export default useNotifications;