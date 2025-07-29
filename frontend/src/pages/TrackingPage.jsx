import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import TripTrackingMap from '../components/tracking/TripTrackingMap';
import TripStatusDisplay from '../components/tracking/TripStatusDisplay';
import ETADisplay from '../components/tracking/ETADisplay';
import NotificationCenter from '../components/tracking/NotificationCenter';
import { trackingService } from '../services/tracking';

const TrackingPage = () => {
  const { tripId } = useParams();
  const [tripInfo, setTripInfo] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load trip information
  useEffect(() => {
    const loadTripInfo = async () => {
      try {
        setIsLoading(true);
        const data = await trackingService.getTripTracking(tripId);
        setTripInfo(data);
        setError(null);
      } catch (err) {
        console.error('Failed to load trip info:', err);
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    if (tripId) {
      loadTripInfo();
    }
  }, [tripId]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading trip information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Trip Not Found</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.history.back()}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => window.history.back()}
                className="mr-4 p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Trip Tracking</h1>
                {tripInfo && (
                  <p className="text-sm text-gray-600">
                    {tripInfo.origin_terminal} → {tripInfo.destination_terminal}
                  </p>
                )}
              </div>
            </div>

            {/* Notification Center */}
            <NotificationCenter tripId={tripId} />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map Section - Takes up 2 columns on large screens */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Live Location</h2>
                <p className="text-sm text-gray-600">Real-time bus tracking</p>
              </div>
              
              <TripTrackingMap 
                tripId={tripId} 
                className="h-96 lg:h-[500px]"
              />
            </div>
          </div>

          {/* Sidebar - Status and ETA */}
          <div className="space-y-6">
            {/* Trip Status */}
            <TripStatusDisplay tripId={tripId} />
            
            {/* ETA Display */}
            <ETADisplay tripId={tripId} />
            
            {/* Trip Information Card */}
            {tripInfo && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Trip Details</h3>
                
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Trip ID:</span>
                    <span className="font-medium">{tripInfo.trip_id}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-500">Bus:</span>
                    <span className="font-medium">{tripInfo.bus_license_plate || 'N/A'}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-500">Driver:</span>
                    <span className="font-medium">{tripInfo.driver_name || 'N/A'}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-500">Passengers:</span>
                    <span className="font-medium">{tripInfo.passengers_count || 0}</span>
                  </div>
                  
                  {tripInfo.distance_remaining && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Distance Left:</span>
                      <span className="font-medium">{tripInfo.distance_remaining.toFixed(1)} km</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Emergency Contact */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-semibold text-red-900 mb-2 flex items-center">
                <span className="mr-2">🚨</span>
                Emergency Contact
              </h3>
              <p className="text-sm text-red-800 mb-2">
                If you need immediate assistance, contact our support team.
              </p>
              <button className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 text-sm font-medium">
                Call Support: +1 (555) 123-4567
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackingPage;