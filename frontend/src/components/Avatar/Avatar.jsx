import React from 'react';
import PropTypes from 'prop-types';

const Avatar = ({ src = null, alt = '',className, shape = 'square', size=32, onClick, ...props  }) => {
  // Use Bootstrap's rounded-circle class to make it round or square
  const shapeClass = shape === 'circle' ? 'rounded-circle' : 'rounded';
  const randomImageUrl = `https://picsum.photos/${size}`;
  return (
    <img 
      src={src || randomImageUrl } 
      className={`mx-auto d-block ${shapeClass} ${className?className:''} img-fluid`} 
      alt={alt}
      style={{ width: `${size}px`, height: `${size}px`, cursor:'pointer', borderRadius:shape==='circle'?'50%':'8px' }} // Adjust to desired size
      onClick={onClick} // Optionally handle click events
        {...props}
    />
  );
};

// Define prop types for the component
Avatar.propTypes = {
  src: PropTypes.string,        // The image source should be a string
  alt: PropTypes.string,        // The alt text should be a string
  shape: PropTypes.oneOf(['square', 'circle']), // Shape should be either 'square' or 'circle'
};

// Default prop values
Avatar.default = {
  src: null,
  alt: '',
  shape: 'square',  // Default shape is square
};

export default Avatar;
