import React, { useState } from 'react';
import { Icon } from '@iconify/react';
import './DatePicker.css';
import { FormInput } from '../../Form/FormInput';
import Button from '../../Button/Button';

// Helper function to get days of the month and the starting day
const generateDays = (month, year) => {
  const date = new Date(year, month, 0);
  const daysInMonth = date.getDate();
  const firstDay = new Date(year, month - 1, 1).getDay(); // Get the day of the week for the 1st of the month
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

const DatePicker = () => {
  // State variables
  const [selectedDate, setSelectedDate] = useState(null);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [isCalendarVisible, setCalendarVisible] = useState(false);

  const handleDateClick = (date) => {
    setSelectedDate(date);
    setCalendarVisible(false); // Close calendar after selection
  };

  const changeMonth = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + direction);
    setCurrentDate(newDate);
  };

  const changeYear = (direction) => {
    const newDate = new Date(currentDate);
    newDate.setFullYear(currentDate.getFullYear() + direction);
    setCurrentDate(newDate);
  };

  // Generate the days for the current month
  const days = generateDays(currentDate.getMonth() + 1, currentDate.getFullYear());

  // Array of day names
  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="date-picker">
      <div className="input-group" onClick={() => setCalendarVisible(!isCalendarVisible)}>
        <FormInput type="text" placeholder={"Select a date"} value={selectedDate ? `${selectedDate}/${currentDate.getMonth() + 1}/${currentDate.getFullYear()}` : ''} />
        <Button className="input-group-btn" variant='primary' round={false} style={{ height: '58px' }}>
          <Icon icon="uit:calender" width="25" height="25" />
        </Button>
      </div>

      {isCalendarVisible && (
        <div className="date-picker-calendar">
          <div className="date-picker-calendar-header">
            <Icon icon="ooui:next-rtl" width="20" height="20" onClick={() => changeMonth(-1)} />
            <Icon icon="iconamoon:player-previous-thin" width="24" height="24" onClick={() => changeYear(-1)} />

            <span>{currentDate.toLocaleString('default', { month: 'long' })} {currentDate.getFullYear()}</span>
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
          <div className="date-picker-calendar-footer border-top">
                
          </div>
        </div>
      )}
    </div>
  );
};

export default DatePicker;
