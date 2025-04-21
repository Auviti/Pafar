import { useState } from "react";
import { FormInput } from "../../components/Form/FormInput";  // Assuming you have a custom FormInput component
import Button from "../../components/Button/Button"; // Assuming you have a custom Button component

const BookingStatus = () => {
  const [bookingId, setBookingId] = useState('');
  const [error, setError] = useState('');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setStatus(null);
    setLoading(true);

    try {
      const response = await fetchBooking({
        baseurl: 'https://literate-cod-9vwgg7xj5qg297w5-8001.app.github.dev',
        id: bookingId,
      });

      setStatus(response.data?.status || 'Unknown');
    } catch (err) {
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="border-lg p-3" style={{ borderRadius: '8px' }} onSubmit={handleSubmit}>
      <div className="row p-1">
        <div className="col-12 p-1">
          <FormInput
            id="bookingId"
            label="Booking ID"
            value={bookingId}
            onChange={(e) => setBookingId(e.target.value)}
          />
        </div>

        <div className="col-12 p-2 d-flex justify-content-center align-items-center">
          <Button type="submit" disabled={loading}>
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && <div className="alert alert-danger mt-2">{error}</div>}

      {/* Result */}
      {status && !error && (
        <div className="mt-3">
          <h5>Booking Status:</h5>
          <p className="text-primary fw-bold">{status}</p>
        </div>
      )}
    </form>
  );
};

export default BookingStatus;

