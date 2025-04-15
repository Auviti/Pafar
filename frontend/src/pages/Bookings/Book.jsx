import { useState } from "react";
import { FormInput, FormRadioButton, FormSelect } from "../../components/Form/FormInput";
import Button from "../../components/Button/Button";
import { filterRides } from "../../services/api/rides"; // your filter API function

const Book = () => {
  const [bookingType, setBookingType] = useState(1); // 0: Round Trip, 1: One Way, 2: Multi City
  const [fromLocation, setFromLocation] = useState('233 S Wacker Dr, Chicago, IL');
  const [toLocation, setToLocation] = useState('Millennium Park, Chicago');
  const [departDate, setDepartDate] = useState('2025-04-14T10:30:00Z');
  const [returnDate, setReturnDate] = useState('2025-04-14T11:00:00Z');
  const [passengers, setPassengers] = useState("1");
  const [travelClass, setTravelClass] = useState('economy');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [rides, setRides] = useState([]); // store API results

  const handleBookingType = (index) => setBookingType(index);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!fromLocation || !toLocation || !departDate || (bookingType !== 1 && !returnDate) || !passengers || !travelClass) {
      setError("Please fill out all required fields.");
      return;
    }

    setError('');
    setLoading(true);

    const filterData = {
      ride_class: travelClass.toUpperCase(),
      ride_type: bookingType === 0 ? "ROUND" : bookingType === 1 ? "ONE_WAY" : "MULTICITY",
      startlocation: fromLocation,
      endlocation: toLocation,
      starts_at:departDate,
      ends_at:returnDate,
      passengers: Number(passengers),
    };

    try {
      const response = await filterRides({
        baseurl: 'https://literate-cod-9vwgg7xj5qg297w5-8001.app.github.dev',
        filterData
      });
      
      setRides(response.data || []);
      setError(response.error || '');
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="border-lg p-1" style={{ borderRadius: '8px' }} onSubmit={handleSubmit}>
      <div className='d-flex justify-content-between align-items-center'>
        <FormRadioButton
          label="Round Trip"
          id="bookingType0"
          name="bookingType"
          value="ROUND"
          checked={bookingType === 0}
          onChange={() => handleBookingType(0)}
        />
        <FormRadioButton
          label="One Way"
          id="bookingType1"
          name="bookingType"
          value="ONE_WAY"
          checked={bookingType === 1}
          onChange={() => handleBookingType(1)}
        />
        <FormRadioButton
          label="Multi City"
          id="bookingType2"
          name="bookingType"
          value="MULTICITY"
          checked={bookingType === 2}
          onChange={() => handleBookingType(2)}
        />
      </div>

      <div className="row p-1">
        <div className="col-12 p-1">
          <FormInput
            id="fromlocation"
            label="From"
            value={fromLocation}
            onChange={(e) => setFromLocation(e.target.value)}
          />
        </div>

        <div className="col-12 p-1">
          <FormInput
            id="tolocation"
            label="To"
            value={toLocation}
            onChange={(e) => setToLocation(e.target.value)}
          />
        </div>

        <div className="col-6 p-1">
          <FormInput
            id="departDate"
            label="Depart"
            type="datetime-local"
            value={departDate}
            onChange={(e) => setDepartDate(e.target.value)}
          />
        </div>

        {bookingType !== 1 && (
          <div className="col-6 p-1">
            <FormInput
              id="returnDate"
              label="Return"
              type="datetime-local"
              value={returnDate}
              onChange={(e) => setReturnDate(e.target.value)}
            />
          </div>
        )}

        <div className="col-6 p-1">
          <FormSelect
            label="Passengers"
            value={passengers}
            onChange={(e) => setPassengers(e.target.value)}
            items={[
              { label: '1', value: '1' },
              { label: '2', value: '2' },
              { label: '3', value: '3' },
              { label: '4', value: '4' },
              { label: '5+', value: '5' },
            ]}
          />
        </div>

        <div className="col-6 p-1">
          <FormSelect
            label="Class"
            value={travelClass}
            onChange={(e) => setTravelClass(e.target.value)}
            items={[
              { label: 'Economy', value: 'economy' },
              { label: 'Business', value: 'business' },
              { label: 'First Class', value: 'firstClass' },
            ]}
          />
        </div>

        <div className="col-12 p-2 d-flex justify-content-center align-items-center">
          <Button type="submit">Search</Button>
        </div>
      </div>

      {error && <div className="alert alert-danger mt-2">{error}</div>}
      {loading && <div className="alert alert-info mt-2">Loading...</div>}

      {rides.length > 0 && (
        <div className="mt-4">
          <h4>Available Rides:</h4>
          <ul>
            {rides.map((ride, idx) => (
              <li key={idx}>{ride.name} - {ride.status}</li>
            ))}
          </ul>
        </div>
      )}
    </form>
  );
};

export default Book;
