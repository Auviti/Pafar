import React, { useState } from 'react';
import PropTypes from 'prop-types'; // Import PropTypes
import { Icon } from '@iconify/react';
import './DatePicker.css';
import { FormInput } from '../../Form/FormInput';
import Button from '../../Button/Button';

function getFormattedDate(format, date) {
  const today = date;

  // Helper function to pad numbers
  const pad = (num) => num < 10 ? '0' + num : num;

  switch (format) {
    case 'ISO':
      return today.toISOString().split('T')[0];
    case 'US':
      return `${pad(today.getMonth() + 1)}/${pad(today.getDate())}/${today.getFullYear()}`;
    case 'EU':
      return `${pad(today.getDate())}/${pad(today.getMonth() + 1)}/${today.getFullYear()}`;
    case 'Full':
      return today.toLocaleString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
    case 'Short':
      return `${pad(today.getMonth() + 1)}/${pad(today.getDate())}/${String(today.getFullYear()).slice(-2)}`;
    case 'Time24':
      return today.toLocaleTimeString('en-GB', { hour12: false });
    case 'Time12':
      return today.toLocaleTimeString('en-US', { hour12: true });
    case 'Dash':
      return `${pad(today.getMonth() + 1)}-${pad(today.getDate())}-${today.getFullYear()}`;
    case 'Unix':
      return today.getTime();
    case 'MonthYear':
      return today.toLocaleString('en-US', { year: 'numeric', month: 'long' });
    case 'Custom':
      return `${today.getFullYear()}/${pad(today.getMonth() + 1)}/${pad(today.getDate())}`;
    case 'FullDateTime':
      return today.toISOString().replace('T', ' ').split('.')[0];
    default:
      return today.toLocaleDateString();
  }
}

// Helper function to get days of the month and the starting day
const generateDays = (month, year) => {
  const date = new Date(year, month, 0);
  const daysInMonth = date.getDate();
  const firstDay = new Date(year, month - 1, 1).getDay();
  const days = [];

  // Add empty slots for the days before the 1st day of the month
  for (let i = 0; i < firstDay; i++) {
    days.push(null);
  }

  // Add the actual days of the month
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }

  return days;
};

const DatePicker = ({ showToday=true, format='EU', onChange }) => {
  const [selectedDate, setSelectedDate] = useState(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [isCalendarVisible, setCalendarVisible] = useState(false);

  const handleDateClick = (date) => {
    setSelectedDate(date);
    setCalendarVisible(false);
    const formattedDate = getFormattedDate(format, new Date(currentDate.getFullYear(), currentDate.getMonth(), date));
    if (onChange) {
      onChange(formattedDate);
    }
  };

  const changeMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + direction);
    setCurrentDate(newDate);
    if (onChange) {
      const formattedDate = getFormattedDate(format, newDate);
      onChange(formattedDate);
    }
  };

  const changeYear = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setFullYear(currentDate.getFullYear() + direction);
    setCurrentDate(newDate);
    if (onChange) {
      const formattedDate = getFormattedDate(format, newDate);
      onChange(formattedDate);
    }
  };

  const days = generateDays(currentDate.getMonth() + 1, currentDate.getFullYear());

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const today = new Date();
  const todayFormatted = getFormattedDate(format, today);

  return (
    <div className="date-picker">
      <div className="input-group" onClick={() => setCalendarVisible(!isCalendarVisible)}>
        <FormInput
          type="text"
          placeholder="Select a date"
          value={selectedDate ? `${selectedDate}/${currentDate.getMonth() + 1}/${currentDate.getFullYear()}` : ''}
        />
        <Button className="input-group-btn" variant="primary" round={false} style={{ height: '58px' }}>
          <Icon icon="uit:calender" width="25" height="25" />
        </Button>
      </div>

      {isCalendarVisible && (
        <div className="date-picker-calendar">
          <div className="date-picker-calendar-header">
            <Icon icon="ooui:next-rtl" width="20" height="20" onClick={() => changeMonth(-1)} />
            <Icon icon="iconamoon:player-previous-thin" width="24" height="24" onClick={() => changeYear(-1)} />
            <span>
              {currentDate.toLocaleString('default', { day: '2-digit', month: 'long' })} {currentDate.getFullYear()}
            </span>
            <Icon icon="iconamoon:player-next-thin" width="24" height="24" onClick={() => changeYear(1)} />
            <Icon icon="ooui:next-ltr" width="20" height="20" onClick={() => changeMonth(1)} />
          </div>
          <div className="date-picker-calendar-header-days">
            {dayNames.map((dayName, index) => (
              <div key={index} className="date-picker-calendar-day-name">
                <small>{dayName}</small>
              </div>
            ))}
          </div>
          <div className="date-picker-calendar-body">
            {days.map((day, index) => (
              <div
                key={index}
                className={`date-picker-calendar-day ${selectedDate === day ? 'selected' : ''} ${day === null ? 'empty-day' : ''}`}
                onClick={() => day && handleDateClick(day)}
              >
                {day ? day : ''}
              </div>
            ))}
          </div>
          {showToday && (
            <div className="date-picker-calendar-footer border-top">
              <span className="text-bold">Today:</span>
              <small>{todayFormatted}</small>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Adding PropTypes for validation
DatePicker.propTypes = {
  showToday: PropTypes.bool, // Whether to show today's date
  format: PropTypes.string,  // The date format (e.g., 'US', 'EU', 'ISO', etc.)
  onChange: PropTypes.func,  // Callback function when the date is selected or changed
};

DatePicker.default = {
  showToday: true, // Default value for showToday is true
  format: 'EU',    // Default format is 'EU'
};

export default DatePicker;
