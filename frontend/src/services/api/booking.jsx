import fetchData from "./fetch";

// Function to fetch all bookings
export const fetchBookings = async ({ baseurl = 'http://localhost:8001' }) => {
    return fetchData('GET', `${baseurl}/api/v1/bookings/`);
};

// Function to fetch a single booking by ID
export const fetchBooking = async ({ baseurl = 'http://localhost:8001', id }) => {
    return fetchData('GET', `${baseurl}/api/v1/bookings/${id}`);
};

// Function to update booking status by ID (using PUT)
export const updateBookingStatus = async ({ baseurl = 'http://localhost:8001', id, statusData }) => {
    return fetchData('PUT', `${baseurl}/api/v1/bookings/${id}/status`, statusData);
};

// Function to protect a booking by ID (using PUT)
export const protectBooking = async ({ baseurl = 'http://localhost:8001', id, protectData }) => {
    return fetchData('PUT', `${baseurl}/api/v1/bookings/${id}/protect`, protectData);
};

// Function to create a new booking (use POST instead of GET)
export const createBooking = async ({ baseurl = 'http://localhost:8001', bookingData }) => {
    return fetchData('POST', `${baseurl}/api/v1/bookings/`, bookingData);
};

// Function to delete a booking by ID (using DELETE)
export const deleteBooking = async ({ baseurl = 'http://localhost:8001', id }) => {
    return fetchData('DELETE', `${baseurl}/api/v1/bookings/${id}`);
};
