import React, { useState, useEffect } from 'react';
import './Places.css';
import ThemeProvider from '../../utils/ThemeProvider';
import { FormInput } from '../../components/Form/FormInput';
import Button from '../../components/Button/Button';
import Pagination from '../../components/Pagination/Pagination';

const Places = ({ header, footer, bottomheader }) => {
  // Array representing the card data with actual image URLs
  const cards = Array.from({ length: 35 }, (_, index) => ({
    title: `Thumbnail ${index + 1}`,
    description: 'This is a wider card with supporting text below as a natural lead-in to additional content. This content is a little bit longer.',
    time: '9 mins',
    imageUrl: `https://picsum.photos/seed/${index}/225/225`, // Example placeholder image URL, with seed to generate different images
  }));

  // State for pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);  // Number of items per page (this can be adjusted)
  

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
      <div className='container-fluid'>
        <section className="py-2 text-center container">
          <div className="row py-lg-4">
            <div className="col-lg-6 col-md-8 mx-auto">
              <h1 className="fw-light">Places You Can Be</h1>
              <p className="lead text-body-secondary">
                Discover a variety of unique places to explore, each with its own charm and appeal.
              </p>
            </div>
          </div>
        </section>

        <div className="album p-2 bg-body-tertiary">
          <form className='places-form mb-3'>
            <div className="input-group">
              <FormInput type="email" label={'Search'} placeholder={'Search'} />
              <Button type='submit' className="input-group-btn" variant='primary' round={false} style={{ height: '58px' }}>
                Search
              </Button>
            </div>
          </form>

          <div className="container-fluid">
            <div className="row row-cols-1 row-cols-sm-2 row-cols-md-3 g-3">
              {/* Map through the currentCards array and render a card for each item */}
              {currentCards.map((card, index) => (
                <div key={index} className="col col-md-4 col-lg-3">
                  <div className="card shadow-sm">
                    {/* Replace the SVG with an actual image */}
                    <img
                      className="card-img-top"
                      src={card.imageUrl}  // Use actual image URL from the card data
                      alt={card.title}     // Alt text for accessibility
                      width="100%"
                      height="225"
                    />
                    <div className="card-body">
                      <p className="card-text text-body-secondary">{card.description}</p>
                      <div className="d-flex justify-content-between align-items-center">
                        <div className="btn-group">
                          <button type="button" className="btn btn-sm btn-outline-secondary">View</button>
                          <button type="button" className="btn btn-sm btn-outline-secondary">Edit</button>
                        </div>
                        <small className="text-body-secondary p-2">{card.time}</small>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pagination Component */}
          <Pagination 
            items={cards} 
            position='center'
            currentPage={currentPage} 
            onSelect={handlePageSelect}
            onPrev={handlePageSelect}
            onNext={handlePageSelect}
            itemsPerPage={itemsPerPage}
          />
        </div>
      </div>
      {footer}
      {bottomheader}
    </ThemeProvider>
  );
};

export default Places;
