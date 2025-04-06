import { useState } from "react";
import { FormInput, FormRadioButton, FormSelect } from "../../components/Form/FormInput";
import Button from "../../components/Button/Button";

const Book = () => {
  const [bookingType, setBookingType] = useState(0); // 0: Round Trip, 1: One Way, 2: Multi City
  const [fromLocation, setFromLocation] = useState('');
  const [toLocation, setToLocation] = useState('');
  const [departDate, setDepartDate] = useState('');
  const [returnDate, setReturnDate] = useState('');
  const [passengers, setPassengers] = useState('');
  const [travelClass, setTravelClass] = useState('');
  const [error, setError] = useState('');

  const handleBookingType = (index) => {
    setBookingType(index);
  };

  // Function to handle form submission
  const handleSubmit = (e) => {
    e.preventDefault(); // Prevent the default form submission

    // Check if all required fields are filled
    if (!fromLocation || !toLocation || !departDate || (bookingType !== 1 && !returnDate) || !passengers || !travelClass) {
      setError('Please fill out all required fields.');
      return;
    }

    // If form is valid, clear error message
    setError('');

    // Handle form data here (e.g., send it to an API or log it)
    console.log('Form submitted with the following data:');
    console.log({
      bookingType,
      fromLocation,
      toLocation,
      departDate,
      returnDate,
      passengers,
      travelClass
    });

    // Example of sending the form data to a backend API (uncomment when backend is ready)
    // fetch('/api/bookings', {
    //   method: 'POST',
    //   body: JSON.stringify({
    //     bookingType,
    //     fromLocation,
    //     toLocation,
    //     departDate,
    //     returnDate,
    //     passengers,
    //     travelClass,
    //   }),
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    // })
    //   .then((response) => response.json())
    //   .then((data) => console.log(data))
    //   .catch((error) => console.error('Error:', error));
  };

  return (
    <form className="border-lg p-1" style={{ borderRadius: '8px' }} onSubmit={handleSubmit}>
      <div className='d-flex justify-content-between align-items-center align-self-center'>
        <div className="mx-0">
            <FormRadioButton
                label="Round Trip"
                id="bookingType0"
                name="bookingType"
                value="Round Trip"
                checked={bookingType === 0}
                onChange={() => handleBookingType(0)}
            />
        </div>
        <div className="mx-2">
            <FormRadioButton
                label="One Way"
                id="bookingType1"
                name="bookingType"
                value="One Way"
                checked={bookingType === 1}
                onChange={() => handleBookingType(1)}
            />
        </div>
        <div className="mx-0">
            <FormRadioButton
                label="Multi City"
                id="bookingType2"
                name="bookingType"
                value="Multi City"
                checked={bookingType === 2}
                onChange={() => handleBookingType(2)}
            />
        </div>
      </div>

      <div className="row p-1">
        <div className="col-12 p-1">
            <FormInput
                id='fromlocation'
                label={'From'}
                value={fromLocation}
                onChange={(e) => setFromLocation(e.target.value)}
            />
        </div>
        <div className="col-12 p-1">
            <FormInput
                id='tolocation'
                label={'To'}
                value={toLocation}
                onChange={(e) => setToLocation(e.target.value)}
            />
        </div>

        <div className="col-6 p-1">
            <FormInput
                id='departDate'
                label={'Depart'}
                type="date"
                value={departDate}
                onChange={(e) => setDepartDate(e.target.value)}
            />
        </div>

        {bookingType !== 1 && (
            <div className="col-6 p-1">
                <FormInput
                    id='returnDate'
                    label={'Return'}
                    type="date"
                    value={returnDate}
                    onChange={(e) => setReturnDate(e.target.value)}
                />
            </div>
        )}

        <div className="col-6 p-1">
            <FormSelect
                label='Passengers'
                value={'1'}
                // onChange={(e) => setPassengers(e.target.value)}
                items={[
                    { label: '1', value: '1' },
                    { label: '2', value: '2' },
                    { label: '3', value: '3' },
                    { label: '4', value: '4' },
                    { label: '5+', value: '5+' },
                ]}
            />
        </div>

        <div className="col-6 p-1">
            <FormSelect
                label='Class'
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

      {/* Display error message if any */}
      {error && <div className="alert alert-danger">{error}</div>}
    </form>
  );
};

export default Book;
