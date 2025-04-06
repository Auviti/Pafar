import { useState } from "react";
import { FormInput } from "../../components/Form/FormInput";  // Assuming you have a custom FormInput component
import Button from "../../components/Button/Button"; // Assuming you have a custom Button component

const BookingStatus = () => {
  const [bookingId, setBookingId] = useState(''); // State to hold the booking ID
  const [error, setError] = useState(''); // State to hold error messages
  const [status, setStatus] = useState(null); // State to hold the booking status result

  // Function to handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault(); // Prevent the default form submission

    if (!bookingId) {
      setError('Booking ID is required.');
      return;
    }

    setError(''); // Clear previous error

    try {
      // Assuming you have an API function to fetch booking status
      const response = await fetch(`/api/booking-status/${bookingId}`);
      const data = await response.json();

      if (response.ok) {
        setStatus(data.status); // Update the status with the response from API
      } else {
        setError(data.message || 'Failed to fetch booking status'); // Display any error from the server
      }
    } catch (error) {
      setError('Error fetching booking status. '+error);
    }
  };

  return (
    <form className="border-lg p-2" style={{ borderRadius: '8px' }} onSubmit={handleSubmit}>
      <div className="row p-1">
        <div className="col-12 p-1">
          <FormInput
            id='bookingId'
            label={'Booking ID'}
            value={bookingId}
            onChange={(e) => setBookingId(e.target.value)}
          />
        </div>

        <div className="col-12 p-2 d-flex justify-content-center align-items-center">
          <Button type="submit">Search</Button>
        </div>
      </div>

      {/* Display Error Message */}
      {error && <div className="alert alert-danger">{error}</div>}

      {/* Display Booking Status if available */}
      {status && (
        <div className="mt-3">
          <h5>Booking Status:</h5>
          <p className={`text-${status||'danger'}`}>{status}</p>
        </div>
      )}
    </form>
  );
};

export default BookingStatus;
