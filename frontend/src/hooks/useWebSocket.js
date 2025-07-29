import { useEffect, useRef, useState, useCallback } from 'react';
import { io } from 'socket.io-client';
import Cookies from 'js-cookie';

const WEBSOCKET_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000';

export const useWebSocket = (tripId = null) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    const token = Cookies.get('access_token');
    if (!token) {
      setConnectionError('Authentication token not found');
      return;
    }

    try {
      socketRef.current = io(WEBSOCKET_URL, {
        auth: {
          token: token
        },
        transports: ['websocket', 'polling'],
        timeout: 10000,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      });

      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionError(null);
        setReconnectAttempts(0);

        // Join trip room if tripId is provided
        if (tripId) {
          socketRef.current.emit('join_trip', { trip_id: tripId });
        }
      });

      socketRef.current.on('disconnect', (reason) => {
        console.log('WebSocket disconnected:', reason);
        setIsConnected(false);
        
        if (reason === 'io server disconnect') {
          // Server initiated disconnect, try to reconnect
          setTimeout(() => connect(), 1000);
        }
      });

      socketRef.current.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        setConnectionError(error.message);
        setIsConnected(false);
        
        // Implement exponential backoff for reconnection
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectAttempts(prev => prev + 1);
          connect();
        }, delay);
      });

      // Generic message handler
      socketRef.current.onAny((eventName, data) => {
        setLastMessage({ event: eventName, data, timestamp: Date.now() });
      });

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionError(error.message);
    }
  }, [tripId, reconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    
    setIsConnected(false);
    setConnectionError(null);
    setReconnectAttempts(0);
  }, []);

  const emit = useCallback((event, data) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot emit event:', event);
    }
  }, []);

  const subscribe = useCallback((event, callback) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback);
      
      // Return unsubscribe function
      return () => {
        if (socketRef.current) {
          socketRef.current.off(event, callback);
        }
      };
    }
    return () => {};
  }, []);

  const joinTrip = useCallback((newTripId) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('join_trip', { trip_id: newTripId });
    }
  }, []);

  const leaveTrip = useCallback((tripIdToLeave) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('leave_trip', { trip_id: tripIdToLeave });
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionError,
    lastMessage,
    emit,
    subscribe,
    joinTrip,
    leaveTrip,
    reconnect: connect,
    disconnect
  };
};

export default useWebSocket;