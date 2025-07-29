import React, { useState, useEffect } from 'react';
import { trackingService } from '../../services/tracking';
import useWebSocket from '../../hooks/useWebSocket';

const TripStatusDisplay = ({ tripId, className = '' }) => {
  const [tripStatus, setTripStatus] = useState(null);
  const [eta, setEta] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const { subscribe, isConnected } = useWebSocket(tripId);

  // Status configuration
  const statusConfig = {
    scheduled: {
      label: 'Scheduled',
      color: 'bg-gray-500',
      icon: '📅',
      description: 'Trip is scheduled and waiting to depart'
    },
    boarding: {
      label: 'Boarding',
      color: 'bg-yellow-500',
      icon: '🚌',
      description: 'Passengers are boarding the bus'
    },
    departed: {
      label: 'Departed',
      color: 'bg-blue-500',
      icon: '🚀',
      description: 'Bus has departed from origin terminal'
    },
    in_transit: {
      label: 'In Transit',
      color: 'bg-green-500',
      icon: '🛣️',
      description: 'Bus is on the way to destination'
    },
    approaching: {
      label: 'Approaching',
      color: 'bg-orange-500',
      icon: '📍',
      description: 'Bus is approaching destination terminal'
    },
    arrived: {
      label: 'Arrived',
      color: 'bg-green-600',
      icon: '✅',
      description: 'Bus has arrived at destination'
    },
    completed: {
      label: 'Completed',
      color: 'bg-gray-600',
      icon: '🏁',
      description: 'Trip has been completed'
    },
    cancelled: {
      label: 'Cancelled',
      color: 'bg-red-500',
      icon: '❌',
      description: 'Trip has been cancelled'
    },
    delayed: {
      label: 'Delayed',
      color: 'bg-red-400',
      icon: '⏰',
      description: 'Trip is running behind schedule'
    }
  };

  // Progress steps for visual indicator
  const progressSteps = [
    { key: 'scheduled', label: 'Scheduled' },
    { key: 'boarding', label: 'Boarding' },
    { key: 'departed', label: 'Departed' },
    { key: 'in_transit', label: 'In Transit' },
    { key: 'approaching', label: 'Approaching' },
    { key: 'arrived', label: 'Arrived' }
  ];

  // Get current step index
  const getCurrentStepIndex = (status) => {
    if (status === 'cancelled') return -1;
    if (status === 'completed') return progressSteps.length;
    return progressSteps.findIndex(step => step.key === status);
  };

  // Load initial trip status
  useEffect(() => {
    const loadTripStatus = async () => {
      try {
        setIsLoading(true);
        const [statusData, etaData] = await Promise.all([
          trackingService.getTripStatus(tripId),
          trackingService.getTripETA(tripId).catch(() => null) // ETA might not be available
        ]);
        
        setTripStatus(statusData);
        setEta(etaData);
        setError(null);
      } catch (err) {
        console.error('Failed to load trip status:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (tripId) {
      loadTripStatus();
    }
  }, [tripId]);

  // Subscribe to real-time status updates
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeStatus = subscribe('trip_status_update', (data) => {
      if (data.trip_id === tripId) {
        setTripStatus(prev => ({
          ...prev,
          status: data.status,
          updated_at: data.timestamp
        }));
      }
    });

    const unsubscribeETA = subscribe('eta_update', (data) => {
      if (data.trip_id === tripId) {
        setEta(data.eta_data);
      }
    });

    return () => {
      unsubscribeStatus();
      unsubscribeETA();
    };
  }, [isConnected, subscribe, tripId]);

  // Format time display
  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Format duration
  const formatDuration = (minutes) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  if (isLoading) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="bg-gray-200 h-6 rounded mb-2"></div>
        <div className="bg-gray-200 h-4 rounded mb-4"></div>
        <div className="flex space-x-2">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-gray-200 h-8 w-8 rounded-full"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <div className="flex items-center">
          <div className="text-red-600 mr-2">⚠️</div>
          <div>
            <p className="text-red-800 font-medium">Failed to load trip status</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!tripStatus) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
        <p className="text-gray-600">No trip status available</p>
      </div>
    );
  }

  const currentStatus = statusConfig[tripStatus.status] || statusConfig.scheduled;
  const currentStepIndex = getCurrentStepIndex(tripStatus.status);

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 ${className}`}>
      {/* Current Status Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <div className={`w-3 h-3 rounded-full ${currentStatus.color} mr-2`}></div>
          <div>
            <h3 className="font-semibold text-gray-900">
              {currentStatus.icon} {currentStatus.label}
            </h3>
            <p className="text-sm text-gray-600">{currentStatus.description}</p>
          </div>
        </div>
        
        {/* Connection indicator */}
        <div className="flex items-center text-xs text-gray-500">
          <div className={`w-2 h-2 rounded-full mr-1 ${isConnected ? 'bg-green-500' : 'bg-gray-400'}`}></div>
          {isConnected ? 'Live' : 'Offline'}
        </div>
      </div>

      {/* Progress Indicator */}
      {tripStatus.status !== 'cancelled' && (
        <div className="mb-4">
          <div className="flex items-center justify-between">
            {progressSteps.map((step, index) => {
              const isCompleted = index < currentStepIndex;
              const isCurrent = index === currentStepIndex;
              const isUpcoming = index > currentStepIndex;

              return (
                <div key={step.key} className="flex flex-col items-center flex-1">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium mb-1 ${
                    isCompleted ? 'bg-green-500 text-white' :
                    isCurrent ? 'bg-blue-500 text-white' :
                    'bg-gray-200 text-gray-500'
                  }`}>
                    {isCompleted ? '✓' : index + 1}
                  </div>
                  <span className={`text-xs text-center ${
                    isCurrent ? 'text-blue-600 font-medium' : 'text-gray-500'
                  }`}>
                    {step.label}
                  </span>
                  
                  {/* Progress line */}
                  {index < progressSteps.length - 1 && (
                    <div className={`absolute h-0.5 w-full mt-4 ${
                      isCompleted ? 'bg-green-500' : 'bg-gray-200'
                    }`} style={{
                      left: '50%',
                      width: `${100 / progressSteps.length}%`,
                      zIndex: -1
                    }}></div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Trip Details */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Departure:</span>
          <div className="font-medium">{formatTime(tripStatus.scheduled_departure)}</div>
        </div>
        
        <div>
          <span className="text-gray-500">Arrival:</span>
          <div className="font-medium">{formatTime(tripStatus.scheduled_arrival)}</div>
        </div>

        {eta && (
          <>
            <div>
              <span className="text-gray-500">ETA:</span>
              <div className="font-medium text-blue-600">{formatTime(eta.estimated_arrival)}</div>
            </div>
            
            <div>
              <span className="text-gray-500">Remaining:</span>
              <div className="font-medium">{formatDuration(eta.remaining_minutes)}</div>
            </div>
          </>
        )}
      </div>

      {/* Delay Warning */}
      {tripStatus.status === 'delayed' && tripStatus.delay_minutes && (
        <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
          <div className="flex items-center text-yellow-800">
            <span className="mr-2">⚠️</span>
            <span className="text-sm">
              Trip is delayed by {tripStatus.delay_minutes} minutes
            </span>
          </div>
        </div>
      )}

      {/* Last Updated */}
      <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500">
        Last updated: {formatTime(tripStatus.updated_at)}
      </div>
    </div>
  );
};

export default TripStatusDisplay;