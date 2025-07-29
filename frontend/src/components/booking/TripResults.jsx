import React, { useState, useMemo } from 'react';

const TripResults = ({ trips = [], loading = false, onSelectTrip }) => {
  const [sortBy, setSortBy] = useState('departure_time');
  const [filterBy, setFilterBy] = useState('all');
  const [priceRange, setPriceRange] = useState({ min: 0, max: 1000 });

  const sortedAndFilteredTrips = useMemo(() => {
    let filtered = [...trips];

    // Apply price filter
    filtered = filtered.filter(trip => 
      trip.fare >= priceRange.min && trip.fare <= priceRange.max
    );

    // Apply availability filter
    if (filterBy === 'available') {
      filtered = filtered.filter(trip => trip.available_seats > 0);
    } else if (filterBy === 'full') {
      filtered = filtered.filter(trip => trip.available_seats === 0);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'departure_time':
          return new Date(a.departure_time) - new Date(b.departure_time);
        case 'price_low':
          return a.fare - b.fare;
        case 'price_high':
          return b.fare - a.fare;
        case 'duration':
          return a.estimated_duration - b.estimated_duration;
        default:
          return 0;
      }
    });

    return filtered;
  }, [trips, sortBy, filterBy, priceRange]);

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatPrice = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="trip-results loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Searching for trips...</p>
        </div>
      </div>
    );
  }

  if (trips.length === 0) {
    return (
      <div className="trip-results empty">
        <div className="empty-state">
          <h3>No trips found</h3>
          <p>Try adjusting your search criteria or selecting different dates.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="trip-results">
      <div className="results-header">
        <div className="results-count">
          <h3>{sortedAndFilteredTrips.length} trips found</h3>
        </div>

        <div className="results-controls">
          <div className="sort-control">
            <label htmlFor="sortBy">Sort by:</label>
            <select
              id="sortBy"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="departure_time">Departure Time</option>
              <option value="price_low">Price (Low to High)</option>
              <option value="price_high">Price (High to Low)</option>
              <option value="duration">Duration</option>
            </select>
          </div>

          <div className="filter-control">
            <label htmlFor="filterBy">Filter:</label>
            <select
              id="filterBy"
              value={filterBy}
              onChange={(e) => setFilterBy(e.target.value)}
            >
              <option value="all">All Trips</option>
              <option value="available">Available Only</option>
              <option value="full">Full Trips</option>
            </select>
          </div>
        </div>
      </div>

      <div className="price-filter">
        <label>Price Range:</label>
        <div className="price-inputs">
          <input
            type="number"
            placeholder="Min"
            value={priceRange.min}
            onChange={(e) => setPriceRange(prev => ({ ...prev, min: Number(e.target.value) }))}
          />
          <span>to</span>
          <input
            type="number"
            placeholder="Max"
            value={priceRange.max}
            onChange={(e) => setPriceRange(prev => ({ ...prev, max: Number(e.target.value) }))}
          />
        </div>
      </div>

      <div className="trips-list">
        {sortedAndFilteredTrips.map((trip) => (
          <div key={trip.id} className="trip-card">
            <div className="trip-info">
              <div className="trip-route">
                <div className="departure">
                  <div className="time">{formatTime(trip.departure_time)}</div>
                  <div className="terminal">{trip.origin_terminal.name}</div>
                  <div className="city">{trip.origin_terminal.city}</div>
                </div>

                <div className="journey">
                  <div className="duration">{formatDuration(trip.estimated_duration)}</div>
                  <div className="line">
                    <div className="dot"></div>
                    <div className="path"></div>
                    <div className="dot"></div>
                  </div>
                </div>

                <div className="arrival">
                  <div className="time">{formatTime(trip.arrival_time)}</div>
                  <div className="terminal">{trip.destination_terminal.name}</div>
                  <div className="city">{trip.destination_terminal.city}</div>
                </div>
              </div>

              <div className="trip-details">
                <div className="bus-info">
                  <span className="bus-model">{trip.bus.model}</span>
                  <span className="bus-plate">{trip.bus.license_plate}</span>
                </div>
                
                <div className="amenities">
                  {trip.bus.amenities && trip.bus.amenities.map((amenity, index) => (
                    <span key={index} className="amenity">{amenity}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="trip-booking">
              <div className="price">
                <span className="amount">{formatPrice(trip.fare)}</span>
                <span className="per-person">per person</span>
              </div>

              <div className="availability">
                <span className={`seats ${trip.available_seats === 0 ? 'full' : ''}`}>
                  {trip.available_seats} seats left
                </span>
              </div>

              <button
                className="select-trip-button"
                onClick={() => onSelectTrip(trip)}
                disabled={trip.available_seats === 0}
              >
                {trip.available_seats === 0 ? 'Fully Booked' : 'Select Seats'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TripResults;