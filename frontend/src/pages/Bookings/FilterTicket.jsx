import { useState } from "react";
import { FormInput, FormRadioButton, FormSelect } from "../../components/Form/FormInput";
import Button from "../../components/Button/Button";
import { filterTickets } from "../../services/api/tickets"; // renamed API function
import { useNavigate } from 'react-router-dom';

const Ticket = () => {
  const navigate = useNavigate();
  const [ticketType, setTicketType] = useState(1); // 0: Round Trip, 1: One Way, 2: Multi City
  const [fromLocation, setFromLocation] = useState('233 S Wacker Dr, Chicago, IL');
  const [toLocation, setToLocation] = useState('Millennium Park, Chicago');
  const [departDate, setDepartDate] = useState('2025-04-14T10:30:00Z');
  const [returnDate, setReturnDate] = useState('2025-04-14T11:00:00Z');
  const [passengers, setPassengers] = useState("1");
  const [travelClass, setTravelClass] = useState('ECONOMY');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [tickets, setTickets] = useState([]); // renamed from rides

  const handleTicketType = (index) => setTicketType(index);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!fromLocation || !toLocation || !departDate || (ticketType !== 1 && !returnDate) || !passengers || !travelClass) {
      setError("Please fill out all required fields.");
      return;
    }

    setError('');
    setLoading(true);

    const filterData = {
      ticket_class: travelClass.toUpperCase(),
      ticket_type: ticketType === 0 ? "ROUND" : ticketType === 1 ? "ONE_WAY" : "MULTICITY",
      startlocation: fromLocation,
      endlocation: toLocation,
      starts_at: departDate,
      ends_at: returnDate,
      passengers: Number(passengers),
    };

    try {
      const response = await filterTickets({
        baseurl: 'https://literate-cod-9vwgg7xj5qg297w5-8001.app.github.dev',
        filterData
      });

      setTickets(response.data || []);
      setError(response.error || '');
      navigate('/tickets', {
        state: {
          tickets: response.data,
          filter: filterData
        }
      });
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
          id="ticketType0"
          name="ticketType"
          value="ROUND"
          checked={ticketType === 0}
          onChange={() => handleTicketType(0)}
        />
        <FormRadioButton
          label="One Way"
          id="ticketType1"
          name="ticketType"
          value="ONE_WAY"
          checked={ticketType === 1}
          onChange={() => handleTicketType(1)}
        />
        <FormRadioButton
          label="Multi City"
          id="ticketType2"
          name="ticketType"
          value="MULTICITY"
          checked={ticketType === 2}
          onChange={() => handleTicketType(2)}
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

        {ticketType !== 1 && (
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
            onChange={(index) => setPassengers(index)}
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
            onChange={(index) => setTravelClass(index)}
            items={[
              { label: 'Economy', value: 'ECONOMY' },
              { label: 'Business', value: 'BUSINESS' },
              { label: 'First Class', value: 'FIRST_CLASS' }
            ]}
          />
        </div>

        <div className="col-12 p-2 d-flex justify-content-center align-items-center">
          <Button type="submit">Search</Button>
        </div>
      </div>
    </form>
  );
};

export default Ticket;
