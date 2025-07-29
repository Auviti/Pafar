import React, { useEffect, useRef, useState, useCallback } from 'react';
import { trackingService } from '../../services/tracking';
import useWebSocket from '../../hooks/useWebSocket';

const TripTrackingMap = ({ tripId, className = '' }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const busMarkerRef = useRef(null);
  const routePolylineRef = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [route, setRoute] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const { subscribe, isConnected } = useWebSocket(tripId);

  // Initialize Google Maps
  const initializeMap = useCallback(async () => {
    if (!window.google || !mapRef.current) return;

    try {
      // Get initial trip data
      const [trackingData, routeData] = await Promise.all([
        trackingService.getTripTracking(tripId),
        trackingService.getTripRoute(tripId)
      ]);

      setCurrentLocation(trackingData.current_location);
      setRoute(routeData);

      // Initialize map
      const mapOptions = {
        zoom: 13,
        center: trackingData.current_location || routeData.origin_coordinates,
        mapTypeId: window.google.maps.MapTypeId.ROADMAP,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'off' }]
          }
        ]
      };

      mapInstanceRef.current = new window.google.maps.Map(mapRef.current, mapOptions);

      // Add route polyline
      if (routeData.route_coordinates) {
        routePolylineRef.current = new window.google.maps.Polyline({
          path: routeData.route_coordinates,
          geodesic: true,
          strokeColor: '#2563eb',
          strokeOpacity: 1.0,
          strokeWeight: 4,
        });
        routePolylineRef.current.setMap(mapInstanceRef.current);
      }

      // Add origin and destination markers
      if (routeData.origin_coordinates) {
        new window.google.maps.Marker({
          position: routeData.origin_coordinates,
          map: mapInstanceRef.current,
          title: routeData.origin_terminal,
          icon: {
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="8" fill="#10b981" stroke="white" stroke-width="2"/>
                <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">S</text>
              </svg>
            `),
            scaledSize: new window.google.maps.Size(24, 24),
          }
        });
      }

      if (routeData.destination_coordinates) {
        new window.google.maps.Marker({
          position: routeData.destination_coordinates,
          map: mapInstanceRef.current,
          title: routeData.destination_terminal,
          icon: {
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="8" fill="#ef4444" stroke="white" stroke-width="2"/>
                <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">E</text>
              </svg>
            `),
            scaledSize: new window.google.maps.Size(24, 24),
          }
        });
      }

      // Add bus marker
      if (trackingData.current_location) {
        updateBusMarker(trackingData.current_location);
      }

      setMapLoaded(true);
      setIsLoading(false);
    } catch (err) {
      console.error('Failed to initialize map:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [tripId]);

  // Update bus marker position
  const updateBusMarker = useCallback((location) => {
    if (!mapInstanceRef.current || !location) return;

    const position = { lat: location.latitude, lng: location.longitude };

    if (busMarkerRef.current) {
      busMarkerRef.current.setPosition(position);
    } else {
      busMarkerRef.current = new window.google.maps.Marker({
        position,
        map: mapInstanceRef.current,
        title: 'Bus Location',
        icon: {
          url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="8" width="24" height="16" rx="4" fill="#3b82f6" stroke="white" stroke-width="2"/>
              <rect x="6" y="10" width="20" height="8" rx="2" fill="white"/>
              <circle cx="10" cy="22" r="2" fill="#374151"/>
              <circle cx="22" cy="22" r="2" fill="#374151"/>
              <rect x="14" y="6" width="4" height="2" rx="1" fill="#3b82f6"/>
            </svg>
          `),
          scaledSize: new window.google.maps.Size(32, 32),
          anchor: new window.google.maps.Point(16, 16),
        }
      });
    }

    // Smoothly pan to new location
    mapInstanceRef.current.panTo(position);
    setCurrentLocation(location);
  }, []);

  // Load Google Maps script
  useEffect(() => {
    const loadGoogleMaps = () => {
      if (window.google) {
        initializeMap();
        return;
      }

      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}&libraries=geometry`;
      script.async = true;
      script.defer = true;
      script.onload = initializeMap;
      script.onerror = () => {
        setError('Failed to load Google Maps');
        setIsLoading(false);
      };
      document.head.appendChild(script);
    };

    loadGoogleMaps();
  }, [initializeMap]);

  // Subscribe to real-time location updates
  useEffect(() => {
    if (!isConnected) return;

    const unsubscribeLocation = subscribe('location_update', (data) => {
      if (data.trip_id === tripId) {
        updateBusMarker(data.location);
      }
    });

    const unsubscribeStatus = subscribe('trip_status_update', (data) => {
      if (data.trip_id === tripId) {
        console.log('Trip status updated:', data.status);
      }
    });

    return () => {
      unsubscribeLocation();
      unsubscribeStatus();
    };
  }, [isConnected, subscribe, tripId, updateBusMarker]);

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center bg-gray-100 rounded-lg ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-red-50 border border-red-200 rounded-lg ${className}`}>
        <div className="text-center p-4">
          <div className="text-red-600 mb-2">
            <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-800 font-medium">Failed to load map</p>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div ref={mapRef} className="w-full h-full rounded-lg" />
      
      {/* Connection status indicator */}
      <div className="absolute top-2 right-2 flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span className="text-xs bg-white px-2 py-1 rounded shadow">
          {isConnected ? 'Live' : 'Offline'}
        </span>
      </div>

      {/* Current location info */}
      {currentLocation && (
        <div className="absolute bottom-2 left-2 bg-white p-2 rounded shadow-lg text-sm">
          <div className="font-medium text-gray-800">Current Location</div>
          <div className="text-gray-600">
            {currentLocation.latitude.toFixed(6)}, {currentLocation.longitude.toFixed(6)}
          </div>
          {currentLocation.speed && (
            <div className="text-gray-600">
              Speed: {Math.round(currentLocation.speed)} km/h
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TripTrackingMap;