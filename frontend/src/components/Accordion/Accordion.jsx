import React from 'react';
import PropTypes from 'prop-types';

import './Accordion.css';
const Accordion = ({ items = [] }) => {
  
  return (
    <div className="accordion accordion-flush" id="accordionExample">
      {items.map((item, index) => (
        <div className="accordion-item" key={index}>
          <h2 className="accordion-header" id={`heading${index}`}>
            <button
              className={`accordion-button`}
              type="button"
              data-bs-toggle="collapse"
              data-bs-target={`#collapse${index}`}
              aria-expanded={index === 0 ? 'true' : 'false'}
              aria-controls={`collapse${index}`}
            >
              {item.header}
            </button>
          </h2>
          <div
            id={`collapse${index}`}
            className={`accordion-collapse collapse ${index === 0 ? 'show' : ''}`}
            aria-labelledby={`heading${index}`}
            data-bs-parent="#accordionExample"
          >
            <div className="accordion-body">
              <p>{item.body?.title}</p>
              <ul>
                {item.body?.contents.map((content, i) => (
                  <li key={i}>{content}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

// PropTypes for validation
Accordion.propTypes = {
  items: PropTypes.arrayOf(
    PropTypes.shape({
      header: PropTypes.string.isRequired,
      body: PropTypes.shape({
        title: PropTypes.string,
        contents: PropTypes.arrayOf(PropTypes.string),
      }).isRequired,
    })
  ).isRequired,
};

export default Accordion;
