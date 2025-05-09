import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import './Bookings.css';
import ThemeProvider from '../../utils/ThemeProvider';
import { FormCheckBox, FormInput, FormSelect } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Pagination from '../../components/Pagination/Pagination';
import useDeviceType from '../../hooks/useDeviceType';
import { Icon } from '@iconify/react';
import { fetchAllTickets } from '../../services/api/tickets';

const Tickets = ({ header, footer, bottomheader }) => {
  const { isMobile, isDesktop } = useDeviceType();
  const location = useLocation();
  const state = location?.state || {};
  const [tickets, setTickets] = useState(state?.tickets || []);
  const [loading, setLoading] = useState(!state.tickets);
  const [error, setError] = useState(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    const getData = async () => {
      setLoading(true);
      try {
        const response = await fetchAllTickets({
          baseurl: 'https://literate-cod-9vwgg7xj5qg297w5-8001.app.github.dev',
        });
        setTickets(response.data || []);
        setError(null);
      } catch (err) {
        setError(err.message || 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    if (!state.tickets || state.tickets.length === 0) {
      getData();
    }
  }, [state.tickets]);

  const currentTickets = tickets.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const handlePageSelect = (pageNumber) => {
    setCurrentPage(pageNumber);
  };

  return (
    <ThemeProvider>
      {header}
      <div className="container-fluid" style={{ height: '50px' }}></div>
      <div className="p-2">
        <div className="container-fluid mt-2 p-1 px-3 border shadow-lg" style={{ borderRadius: '8px' }}>
          <div className="row align-items-center my-2">
            <div className={`d-flex justify-content-between align-items-center col-lg-4 col-md-12 text-center ${!isDesktop ? 'border-bottom' : 'border-end'} p-1`}>
              <span className="w-50">
                <div className="text-start">From</div>
                <FormInput disabled value={state?.filter?.starts_at} />
              </span>
              <Icon icon="wi:direction-right" width="30" height="30" className="text-light bg-primary mt-4 m-1" style={{ borderRadius: '50%' }} />
              <span className="w-50">
                <div className="text-start">To</div>
                <FormInput disabled value={state?.filter?.ends_at} />
              </span>
            </div>

            <div className={`col-lg-4 col-md-12 text-center text-lg-start ${!isDesktop ? 'border-bottom' : 'border-end'} p-1`}>
              <div className="d-flex justify-content-end align-items-end">
                <span className="mx-1">Return</span>
                <FormCheckBox id="flexSwitchCheckChecked" checked={state?.filter?.ticket_type === "ROUND"} />
              </div>
              <FormInput label="Departure date" value={state?.filter?.starts_at} />
            </div>

            <div className="d-flex justify-content-between align-items-center col-lg-4 col-md-12 p-1">
              <span className="w-50">
                <div className="text-start">Departure (from)</div>
                <FormSelect disabled />
              </span>
              <Icon icon="wi:direction-right" width="30" height="30" className="text-light bg-primary mt-4 m-1" style={{ borderRadius: '50%' }} />
              <span className="w-50">
                <div className="text-start">Arrival (to)</div>
                <FormSelect disabled />
              </span>
            </div>
          </div>
        </div>

        <div className="container-fluid p-0 pt-4">
          <h5 className="card-title">Tickets:</h5>

          {loading && <p className="text-muted">Loading Tickets...</p>}
          {error && <p className="text-danger">{error}</p>}
          {!loading && currentTickets.length === 0 && <p className="text-danger">No Tickets found.</p>}

          {currentTickets.map((ticket, index) => (
            <div key={index} className="card shadow-lg rounded-lg my-2">
              <div className="card-body text-body-secondary">
                <div className="d-flex justify-content-between align-items-center text-center text-dark p-1">
                  <span className="w-50">
                    <div className="text-start">Departure - {ticket.currentlocation}</div>
                    <FormInput value={ticket.departure_time || '10:00 AM'} disabled style={{ fontWeight: 'bold' }} />
                  </span>
                  <span className="badge bg-dark mt-4">{ticket.duration || '4hr.30mins'}</span>
                  <span className="w-50">
                    <div className="text-start">Arrival - {ticket.endlocation}</div>
                    <FormInput value={ticket.arrival_time || '2:30 PM'} disabled style={{ fontWeight: 'bold' }} />
                  </span>
                </div>

                <div className="d-flex justify-content-between align-items-center text-center text-dark p-1">
                  <Button outline variant="danger" className="mx-1">
                    passengers left {ticket.passengers_left ?? ticket.passengers ?? 25}
                  </Button>
                  <Button outline variant="danger" className="mx-1">
                    {ticket?.ticket_class}
                  </Button>
                  <Button outline variant="danger" className="mx-1">
                    {ticket?.ticket_type}
                  </Button>
                  <Button outline variant="info" className="mx-1">
                    View
                  </Button>
                </div>

                <div className="d-flex justify-content-between align-items-center text-center text-dark p-1">
                  <Button outline variant="danger" className="mx-1">
                    fare: {ticket.trip_fare}
                  </Button>
                </div>

                <div className="mt-3">
                  <strong>Stops:</strong>
                  <ul className="stops border bg-light p-3 d-flex justify-content-between" style={{ borderRadius: '8px' }}>
                    {(ticket.stops || ['Stop 1', 'Stop 2', 'Stop 3', 'Stop 4']).map((stop, i) => (
                      <li key={i} className={i === 0 ? 'text-success' : i === 3 ? 'text-danger' : ''}>{stop}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          ))}

          <Pagination
            items={tickets}
            position="center"
            currentPage={currentPage}
            onSelect={handlePageSelect}
            onPrev={() => handlePageSelect(currentPage - 1)}
            onNext={() => handlePageSelect(currentPage + 1)}
            itemsPerPage={itemsPerPage}
          />
        </div>
      </div>
      {footer}
      {bottomheader}
    </ThemeProvider>
  );
};

export default Tickets;
