import React, { useState, useEffect } from 'react';

const SeatMap = ({ 
  trip, 
  selectedSeats = [], 
  onSeatSelect, 
  maxSeats = 1,
  loading = false 
}) => {
  const [seatLayout, setSeatLayout] = useState([]);
  const [occupiedSeats, setOccupiedSeats] = useState([]);

  useEffect(() => {
    if (trip) {
      generateSeatLayout();
      setOccupiedSeats(trip.occupied_seats || []);
    }
  }, [trip]);

  const generateSeatLayout = () => {
    const capacity = trip.bus.capacity;
    const seatsPerRow = 4; // 2 seats on each side of aisle
    const rows = Math.ceil(capacity / seatsPerRow);
    
    const layout = [];
    let seatNumber = 1;

    for (let row = 0; row < rows; row++) {
      const rowSeats = [];
      
      // Left side seats (A, B)
      for (let col = 0; col < 2; col++) {
        if (seatNumber <= capacity) {
          rowSeats.push({
            number: seatNumber,
            position: col === 0 ? 'A' : 'B',
            side: 'left'
          });
          seatNumber++;
        }
      }

      // Aisle space
      rowSeats.push({ type: 'aisle' });

      // Right side seats (C, D)
      for (let col = 0; col < 2; col++) {
        if (seatNumber <= capacity) {
          rowSeats.push({
            number: seatNumber,
            position: col === 0 ? 'C' : 'D',
            side: 'right'
          });
          seatNumber++;
        }
      }

      layout.push(rowSeats);
    }

    setSeatLayout(layout);
  };

  const getSeatStatus = (seatNumber) => {
    if (occupiedSeats.includes(seatNumber)) return 'occupied';
    if (selectedSeats.includes(seatNumber)) return 'selected';
    return 'available';
  };

  const handleSeatClick = (seatNumber) => {
    if (occupiedSeats.includes(seatNumber)) return;

    const isSelected = selectedSeats.includes(seatNumber);
    
    if (isSelected) {
      // Deselect seat
      onSeatSelect(selectedSeats.filter(seat => seat !== seatNumber));
    } else {
      // Select seat
      if (selectedSeats.length < maxSeats) {
        onSeatSelect([...selectedSeats, seatNumber]);
      } else {
        // Replace last selected seat if at max capacity
        const newSelection = [...selectedSeats.slice(0, maxSeats - 1), seatNumber];
        onSeatSelect(newSelection);
      }
    }
  };

  const getSeatIcon = (status) => {
    switch (status) {
      case 'occupied':
        return '🚫';
      case 'selected':
        return '✅';
      default:
        return '💺';
    }
  };

  if (loading) {
    return (
      <div className="seat-map loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading seat map...</p>
        </div>
      </div>
    );
  }

  if (!trip) {
    return (
      <div className="seat-map empty">
        <p>Please select a trip to view seat map</p>
      </div>
    );
  }

  return (
    <div className="seat-map">
      <div className="seat-map-header">
        <h3>Select Your Seats</h3>
        <div className="trip-info">
          <p><strong>{trip.origin_terminal.name}</strong> → <strong>{trip.destination_terminal.name}</strong></p>
          <p>{trip.bus.model} - {trip.bus.license_plate}</p>
        </div>
      </div>

      <div className="seat-legend">
        <div className="legend-item">
          <span className="legend-icon">💺</span>
          <span>Available</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">✅</span>
          <span>Selected</span>
        </div>
        <div className="legend-item">
          <span className="legend-icon">🚫</span>
          <span>Occupied</span>
        </div>
      </div>

      <div className="bus-layout">
        <div className="bus-front">
          <div className="driver-area">🚗 Driver</div>
        </div>

        <div className="seats-container">
          {seatLayout.map((row, rowIndex) => (
            <div key={rowIndex} className="seat-row">
              <div className="row-number">{rowIndex + 1}</div>
              
              {row.map((seat, seatIndex) => {
                if (seat.type === 'aisle') {
                  return <div key={seatIndex} className="aisle"></div>;
                }

                const status = getSeatStatus(seat.number);
                const isClickable = status !== 'occupied';

                return (
                  <button
                    key={seatIndex}
                    className={`seat ${status} ${seat.side}`}
                    onClick={() => handleSeatClick(seat.number)}
                    disabled={!isClickable}
                    title={`Seat ${seat.number}${seat.position} - ${status}`}
                  >
                    <span className="seat-icon">{getSeatIcon(status)}</span>
                    <span className="seat-number">{seat.number}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>

        <div className="bus-back">
          <div className="back-area">Back</div>
        </div>
      </div>

      <div className="selection-summary">
        <div className="selected-seats">
          <h4>Selected Seats ({selectedSeats.length}/{maxSeats}):</h4>
          {selectedSeats.length > 0 ? (
            <div className="selected-list">
              {selectedSeats.map(seatNumber => (
                <span key={seatNumber} className="selected-seat-tag">
                  Seat {seatNumber}
                  <button 
                    onClick={() => handleSeatClick(seatNumber)}
                    className="remove-seat"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p>No seats selected</p>
          )}
        </div>

        {maxSeats > 1 && (
          <div className="selection-tip">
            <p>💡 You can select up to {maxSeats} seats for your booking</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SeatMap;