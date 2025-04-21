import fetchData from "./fetch";

// Function to fetch all tickets with pagination
export const fetchAllTickets = async ({ baseurl = 'http://localhost:8001', skip = 0, limit = 12 }) => {
    return fetchData('GET', `${baseurl}/api/v1/tickets/?skip=${skip}&limit=${limit}`);
};

// Function to fetch a single ticket by ID
export const fetchTicket = async ({ baseurl = 'http://localhost:8001', ticketId }) => {
    return fetchData('GET', `${baseurl}/api/v1/tickets/${ticketId}`);
};

// Function to create a new ticket
export const createTicket = async ({ baseurl = 'http://localhost:8001', ticketData }) => {
    return fetchData('POST', `${baseurl}/api/v1/tickets/`, ticketData);
};

// Function to update ticket details by ID
export const updateTicket = async ({ baseurl = 'http://localhost:8001', ticketId, ticketData }) => {
    return fetchData('PUT', `${baseurl}/api/v1/tickets/${ticketId}`, ticketData);
};

// Function to update the status of a ticket by ID
export const updateTicketStatus = async ({ baseurl = 'http://localhost:8001', ticketId, statusData }) => {
    return fetchData('PUT', `${baseurl}/api/v1/tickets/${ticketId}/status`, statusData);
};

// Function to update the bus of a ticket by ID
export const updateTicketBus = async ({ baseurl = 'http://localhost:8001', ticketId, busId }) => {
    return fetchData('PUT', `${baseurl}/api/v1/tickets/${ticketId}/bus`, { busId });
};

// Function to update the location of a ticket by ID
export const updateTicketLocation = async ({ baseurl = 'http://localhost:8001', ticketId, locationData, isStartLocation = false }) => {
    return fetchData('PUT', `${baseurl}/api/v1/tickets/${ticketId}/location`, { location: locationData, is_start_location: isStartLocation });
};

// Function to delete a ticket by ID
export const deleteTicket = async ({ baseurl = 'http://localhost:8001', ticketId }) => {
    return fetchData('DELETE', `${baseurl}/api/v1/tickets/${ticketId}`);
};

// Function to calculate the fare of a ticket by ID
export const calculateTicketFare = async ({ baseurl = 'http://localhost:8001', ticketId }) => {
    return fetchData('GET', `${baseurl}/api/v1/tickets/${ticketId}/fare`);
};

// Function to get the duration of a ticket by ID
export const getTicketDuration = async ({ baseurl = 'http://localhost:8001', ticketId }) => {
    return fetchData('GET', `${baseurl}/api/v1/tickets/${ticketId}/duration`);
};

// Function to filter tickets by dynamic criteria
export const filterTickets = async ({ baseurl = 'http://localhost:8001', filterData }) => {
    return fetchData('POST', `${baseurl}/api/v1/tickets/filter`, filterData);
};
