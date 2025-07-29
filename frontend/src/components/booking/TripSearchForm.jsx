import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { bookingService } from '../../services/booking';

const searchSchema = z.object({
  originTerminalId: z.string().min(1, 'Please select origin terminal'),
  destinationTerminalId: z.string().min(1, 'Please select destination terminal'),
  departureDate: z.string().min(1, 'Please select departure date'),
  passengers: z.number().min(1, 'At least 1 passenger required').max(10, 'Maximum 10 passengers allowed')
});

const TripSearchForm = ({ onSearch, loading = false }) => {
  const [terminals, setTerminals] = useState([]);
  const [loadingTerminals, setLoadingTerminals] = useState(true);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue
  } = useForm({
    resolver: zodResolver(searchSchema),
    defaultValues: {
      passengers: 1,
      departureDate: new Date().toISOString().split('T')[0]
    }
  });

  const originTerminalId = watch('originTerminalId');
  const destinationTerminalId = watch('destinationTerminalId');

  useEffect(() => {
    loadTerminals();
  }, []);

  const loadTerminals = async () => {
    try {
      setLoadingTerminals(true);
      const data = await bookingService.getTerminals();
      setTerminals(data.terminals || []);
    } catch (error) {
      console.error('Failed to load terminals:', error);
    } finally {
      setLoadingTerminals(false);
    }
  };

  const onSubmit = (data) => {
    if (data.originTerminalId === data.destinationTerminalId) {
      alert('Origin and destination terminals cannot be the same');
      return;
    }
    onSearch(data);
  };

  const swapTerminals = () => {
    const origin = originTerminalId;
    const destination = destinationTerminalId;
    setValue('originTerminalId', destination);
    setValue('destinationTerminalId', origin);
  };

  const today = new Date().toISOString().split('T')[0];
  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + 90);
  const maxDateStr = maxDate.toISOString().split('T')[0];

  return (
    <div className="trip-search-form">
      <div className="search-form-header">
        <h2>Search Trips</h2>
        <p>Find and book your perfect journey</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="search-form">
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="originTerminalId">From</label>
            <select
              id="originTerminalId"
              {...register('originTerminalId')}
              disabled={loadingTerminals}
              className={errors.originTerminalId ? 'error' : ''}
            >
              <option value="">Select origin terminal</option>
              {terminals.map((terminal) => (
                <option key={terminal.id} value={terminal.id}>
                  {terminal.name} - {terminal.city}
                </option>
              ))}
            </select>
            {errors.originTerminalId && (
              <span className="error-message">{errors.originTerminalId.message}</span>
            )}
          </div>

          <div className="swap-button-container">
            <button
              type="button"
              onClick={swapTerminals}
              className="swap-button"
              disabled={!originTerminalId || !destinationTerminalId}
              title="Swap origin and destination"
            >
              ⇄
            </button>
          </div>

          <div className="form-group">
            <label htmlFor="destinationTerminalId">To</label>
            <select
              id="destinationTerminalId"
              {...register('destinationTerminalId')}
              disabled={loadingTerminals}
              className={errors.destinationTerminalId ? 'error' : ''}
            >
              <option value="">Select destination terminal</option>
              {terminals.map((terminal) => (
                <option key={terminal.id} value={terminal.id}>
                  {terminal.name} - {terminal.city}
                </option>
              ))}
            </select>
            {errors.destinationTerminalId && (
              <span className="error-message">{errors.destinationTerminalId.message}</span>
            )}
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="departureDate">Departure Date</label>
            <input
              type="date"
              id="departureDate"
              {...register('departureDate')}
              min={today}
              max={maxDateStr}
              className={errors.departureDate ? 'error' : ''}
            />
            {errors.departureDate && (
              <span className="error-message">{errors.departureDate.message}</span>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="passengers">Passengers</label>
            <select
              id="passengers"
              {...register('passengers', { valueAsNumber: true })}
              className={errors.passengers ? 'error' : ''}
            >
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                <option key={num} value={num}>
                  {num} {num === 1 ? 'Passenger' : 'Passengers'}
                </option>
              ))}
            </select>
            {errors.passengers && (
              <span className="error-message">{errors.passengers.message}</span>
            )}
          </div>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="search-button"
            disabled={loading || loadingTerminals}
          >
            {loading ? 'Searching...' : 'Search Trips'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TripSearchForm;