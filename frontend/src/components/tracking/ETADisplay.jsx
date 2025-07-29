import React, { useState, useEffect } from 'react';
import { trackingService } from '../../services/tracking';
import useWebSocket from '../../hooks/useWebSocket';

const ETADisplay = ({ tripId, className = '' }) => {
  const [eta, setEta] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const { subscribe, isConnected } = useWebSocket(tripId);

  // Load initial ETA
  useEffect(() => {
    const loadETA = async () => {
      try {
        setIsLoading(true);
        const etaData = await trackingService.getTripETA(tripId);
        setEta(etaData);
        setLastUpdated(new Date());
        setError(null);
      } catch (err) {
        console.error('Failed to load ETA:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (tripId) {
      loadETA();
    }
  }, [tripId]);

  // Subscribe to real-time ETA updates
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeETA = subscribe('eta_update', (data) => {
      if (data.trip_id === tripId) {
        setEta(data.eta_data);
        setLastUpdated(new Date());
      }
    });

    return unsubscribeETA;
  }, [isConnected, subscribe, tripId]);

  // Format time
  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Format duration
  const formatDuration = (minutes) => {
    if (!minutes || minutes < 0) return 'N/A';
    
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  // Get delay status
  const getDelayStatus = () => {
    if (!eta || !eta.scheduled_arrival || !eta.estimated_arrival) return null;
    
    const scheduled = new Date(eta.scheduled_arrival);
    const estimated = new Date(eta.estimated_arrival);
    const delayMinutes = Math.round((estimated - scheduled) / 60000);
    
    if (delayMinutes > 5) {
      return { type: 'delayed', minutes: delayMinutes };
    } else if (delayMinutes < -5) {
      return { type: 'early', minutes: Math.abs(delayMinutes) };
    }
    return { type: 'on_time', minutes: 0 };
  };

  // Get time until arrival
  const getTimeUntilArrival = () => {
    if (!eta || !eta.estimated_arrival) return null;
    
    const now = new Date();
    const arrival = new Date(eta.estimated_arrival);
    const diffMinutes = Math.round((arrival - now) / 60000);
    
    return diffMinutes;
  };

  if (isLoading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="bg-gray-200 h-6 rounded mb-2"></div>
        <div className="bg-gray-200 h-4 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center">
          <div className="text-red-600 mr-2">⚠️</div>
          <div>
            <p className="text-red-800 font-medium text-sm">ETA unavailable</p>
            <p className="text-red-600 text-xs">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!eta) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-3 ${className}`}>
        <p className="text-gray-600 text-sm">ETA information not available</p>
      </div>
    );
  }

  const delayStatus = getDelayStatus();
  const timeUntilArrival = getTimeUntilArrival();

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900 flex items-center">
          <span className="mr-2">🕐</span>
          Estimated Arrival
        </h3>
        
        {/* Live indicator */}
        <div className="flex items-center text-xs text-gray-500">
          <div className={`w-2 h-2 rounded-full mr-1 ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
          {isConnected ? 'Live' : 'Offline'}
        </div>
      </div>

      {/* Main ETA Display */}
      <div className="text-center mb-4">
        <div className="text-2xl font-bold text-blue-600 mb-1">
          {formatTime(eta.estimated_arrival)}
        </div>
        
        {timeUntilArrival !== null && timeUntilArrival > 0 && (
          <div className="text-sm text-gray-600">
            in {formatDuration(timeUntilArrival)}
          </div>
        )}
        
        {timeUntilArrival !== null && timeUntilArrival <= 0 && (
          <div className="text-sm text-green-600 font-medium">
            Arrived or arriving now
          </div>
        )}
      </div>

      {/* Delay Status */}
      {delayStatus && (
        <div className={`p-2 rounded-lg mb-3 ${
          delayStatus.type === 'delayed' ? 'bg-red-50 border border-red-200' :
          delayStatus.type === 'early' ? 'bg-green-50 border border-green-200' :
          'bg-blue-50 border border-blue-200'
        }`}>
          <div className={`flex items-center text-sm ${
            delayStatus.type === 'delayed' ? 'text-red-800' :
            delayStatus.type === 'early' ? 'text-green-800' :
            'text-blue-800'
          }`}>
            <span className="mr-2">
              {delayStatus.type === 'delayed' ? '⏰' : 
               delayStatus.type === 'early' ? '⚡' : '✅'}
            </span>
            <span>
              {delayStatus.type === 'delayed' && `Running ${delayStatus.minutes} minutes late`}
              {delayStatus.type === 'early' && `Running ${delayStatus.minutes} minutes early`}
              {delayStatus.type === 'on_time' && 'On schedule'}
            </span>
          </div>
        </div>
      )}

      {/* Details Grid */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-gray-500 block">Scheduled:</span>
          <span className="font-medium">{formatTime(eta.scheduled_arrival)}</span>
        </div>
        
        <div>
          <span className="text-gray-500 block">Distance:</span>
          <span className="font-medium">
            {eta.remaining_distance ? `${eta.remaining_distance.toFixed(1)} km` : 'N/A'}
          </span>
        </div>
        
        <div>
          <span className="text-gray-500 block">Avg Speed:</span>
          <span className="font-medium">
            {eta.average_speed ? `${Math.round(eta.average_speed)} km/h` : 'N/A'}
          </span>
        </div>
        
        <div>
          <span className="text-gray-500 block">Traffic:</span>
          <span className={`font-medium ${
            eta.traffic_condition === 'heavy' ? 'text-red-600' :
            eta.traffic_condition === 'moderate' ? 'text-yellow-600' :
            'text-green-600'
          }`}>
            {eta.traffic_condition ? 
              eta.traffic_condition.charAt(0).toUpperCase() + eta.traffic_condition.slice(1) : 
              'Normal'
            }
          </span>
        </div>
      </div>

      {/* Confidence Indicator */}
      {eta.confidence_level && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Accuracy:</span>
            <div className="flex items-center">
              <div className="w-16 bg-gray-200 rounded-full h-1.5 mr-2">
                <div 
                  className={`h-1.5 rounded-full ${
                    eta.confidence_level >= 80 ? 'bg-green-500' :
                    eta.confidence_level >= 60 ? 'bg-yellow-500' :
                    'bg-red-500'
                  }`}
                  style={{ width: `${eta.confidence_level}%` }}
                ></div>
              </div>
              <span className="text-gray-600">{eta.confidence_level}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-500 text-center">
          Updated {lastUpdated.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
};

export default ETADisplay;