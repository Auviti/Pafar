import React, { useState } from 'react';
import './Bookings.css';
import ThemeProvider from '../../utils/ThemeProvider';
import { FormCheckBox, FormInput, FormSelect } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Pagination from '../../components/Pagination/Pagination';
import useDeviceType from '../../hooks/useDeviceType';
import { Icon } from '@iconify/react/dist/iconify.js';
import { fetchBookings } from '../../services/api/booking';

const Bookings = ({ header, footer, bottomheader }) => {
  const { isMobile, isDesktop } = useDeviceType();
  // const { loading, data: bookings, error } = await fetchBookings({ baseurl: 'http://localhost:5000' });

  // Array representing the card data with actual image URLs
  const cards = Array.from({ length: 35 }, (_, index) => ({
    title: `Thumbnail-${index + 1}`,
    description:
      'This is a wider card with supporting text below as a natural lead-in to additional content. This content is a little bit longer.',
    time: '9 mins',
    imageUrl: `https://picsum.photos/seed/${index}/225/225`, // Example placeholder image URL, with seed to generate different images
  }));

  // State for pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10); // Number of items per page (this can be adjusted)

  // Get the current cards to display based on the page number and items per page
  const currentCards = cards.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Handle page selection from pagination
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
            <div
              className={`d-flex justify-content-between align-items-center col-lg-4 col-md-12 col-12 text-center  ${
                !isDesktop ? 'border-bottom' :'border-end'
              } text-dark p-1`}
            >
              <span className={'w-50'}>
                <div className="d-flex justify-content-start align-items-start">from</div>
                <FormSelect disabled={true} />
              </span>
              <Icon
                icon="wi:direction-right"
                width="30"
                height="30"
                className="text-light bg-primary mt-4 m-1"
                style={{ borderRadius: '50%' }}
              />
              <span className={'w-50'}>
                <div className="d-flex justify-content-start align-items-start">to</div>
                <FormSelect disabled={true} />
              </span>
            </div>

            <div
              className={`col-lg-4 col-md-12 col-12 text-center text-lg-start ${!isDesktop ? 'border-bottom':'border-end'} text-dark p-1`}
            >
              <div className="d-flex justify-content-end align-items-end">
                <span className="mx-1">return</span>
                <FormCheckBox id="flexSwitchCheckChecked" />
              </div>
              <FormInput label={'departure date'} />
            </div>
            <div
              className={`d-flex justify-content-between align-items-center col-lg-4 col-md-12 col-12 text-center text-dark p-1`}
            >
              <span className={'w-50'}>
                <div className="d-flex justify-content-start align-items-start">Departure (from)</div>
                <FormSelect disabled={true} />
              </span>
              <Icon
                icon="wi:direction-right"
                width="30"
                height="30"
                className="text-light bg-primary mt-4 m-1 "
                style={{ borderRadius: '50%' }}
              />
              <span className={'w-50'}>
                <div className="d-flex justify-content-start align-items-start">Arrival (to)</div>
                <FormSelect disabled={true} />
              </span>
            </div>
          </div>
        </div>
        <div className="container-fluid p-0 pt-4">
          <h5 className="card-title">Trips:</h5>

          {currentCards.map((item, index) => (
            <div key={index} className="card shadow-lg rounded-lg my-2">
              <div className="card-body text-body-secondary">
                <div className={`d-flex justify-content-between align-items-center text-center text-dark p-1`}>
                  <span className={'w-50'}>
                    <div className="d-flex justify-content-start align-items-start">lagos bus station(from)</div>
                    <FormInput value={'10:00 AM'} disabled={true} style={{ fontWeight: 'bold' }} />
                  </span>
                  <span className="badge badge-dark mt-4 text-center" style={{ fontWeight: 'bold', color:'black' }}>4hr.30mins</span>
                  <span className={'w-50'}>
                    <div className="d-flex justify-content-start align-items-start">abuja bus station(to)</div>
                    <FormInput value={'2:30 PM'} disabled={true} style={{ fontWeight: 'bold' }} />
                  </span>
                </div>

                <div className={`d-flex justify-content-between align-items-center text-center text-dark p-1`}>
                  <Button outline variant="danger" className={'mx-2'}>
                    passengers left 25
                  </Button>
                  <Button
                    outline
                    variant="info"
                    className={'mx-2'}
                  >
                    View
                  </Button>
                  
                </div>

                <div className="mt-3">
                  <strong>Stops:</strong>
                  <ul className='stops border-lg bg-light p-3 d-flex justify-content-space-between'  style={{borderRadius: '8px' }}>
                    <li className='text-success'>Stop 1</li>
                    <li>Stop 2</li>
                    <li>Stop 3</li>
                    <li className='text-danger'>Stop 4</li>
                  </ul>
                </div>
              </div>
            </div>
          ))}

          {/* Pagination Component */}
          <Pagination
            items={cards}
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

export default Bookings;
