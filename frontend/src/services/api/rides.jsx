import fetchData from "./fetch";

// Function to fetch all rides with pagination
export const fetchAllRides = async ({ baseurl = 'http://localhost:8001', skip = 0, limit = 100 }) => {
    return fetchData('GET', `${baseurl}/api/v1/rides/?skip=${skip}&limit=${limit}`);
};

// Function to fetch a single ride by ID
export const fetchRide = async ({ baseurl = 'http://localhost:8001', rideId }) => {
    return fetchData('GET', `${baseurl}/api/v1/rides/${rideId}`);
};

// Function to create a new ride
export const createRide = async ({ baseurl = 'http://localhost:8001', rideData }) => {
    return fetchData('POST', `${baseurl}/api/v1/rides/`, rideData);
};

// Function to update ride details by ID
export const updateRide = async ({ baseurl = 'http://localhost:8001', rideId, rideData }) => {
    return fetchData('PUT', `${baseurl}/api/v1/rides/${rideId}`, rideData);
};

// Function to update the status of a ride by ID
export const updateRideStatus = async ({ baseurl = 'http://localhost:8001', rideId, statusData }) => {
    return fetchData('PUT', `${baseurl}/api/v1/rides/${rideId}/status`, statusData);
};

// Function to update the bus of a ride by ID
export const updateRideBus = async ({ baseurl = 'http://localhost:8001', rideId, busId }) => {
    return fetchData('PUT', `${baseurl}/api/v1/rides/${rideId}/bus`, { busId });
};

// Function to update the location of a ride by ID
export const updateRideLocation = async ({ baseurl = 'http://localhost:8001', rideId, locationData, isStartLocation = false }) => {
    return fetchData('PUT', `${baseurl}/api/v1/rides/${rideId}/location`, { location: locationData, is_start_location: isStartLocation });
};

// Function to delete a ride by ID
export const deleteRide = async ({ baseurl = 'http://localhost:8001', rideId }) => {
    return fetchData('DELETE', `${baseurl}/api/v1/rides/${rideId}`);
};

// Function to calculate the fare of a ride by ID
export const calculateRideFare = async ({ baseurl = 'http://localhost:8001', rideId }) => {
    return fetchData('GET', `${baseurl}/api/v1/rides/${rideId}/fare`);
};

// Function to get the duration of a ride by ID
export const getRideDuration = async ({ baseurl = 'http://localhost:8001', rideId }) => {
    return fetchData('GET', `${baseurl}/api/v1/rides/${rideId}/duration`);
};

// Function to filter rides by dynamic criteria
export const filterRides = async ({ baseurl = 'http://localhost:8001', filterData }) => {
    return fetchData('POST', `${baseurl}/api/v1/rides/filter`, filterData);
};
