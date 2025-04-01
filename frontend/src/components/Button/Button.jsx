import React from 'react';
import PropTypes from 'prop-types';
import './Button.css';
import Spinner from '../Spinner/Spinner';

const Button = ({ 
  type = 'button', 
  className,
  children, 
  text, 
  size = 'lg', 
  variant = 'primary', 
  outline, 
  onClick, 
  style = {},
  loading = false,
  ...props 
}) => {
  return (
    <button 
      type={type}
      className={`btn ${outline ? `btn-outline-${variant}` : `btn-${variant}`} btn-${size} ${className}`} 
      style={style}
      onClick={onClick} 
      disabled={loading} // Disable the button when loading
      {...props}
    >
        <span className='d-flex justify-content-space-between align-items-center'>
          {loading && <Spinner outline={outline} size={'sm'} /> } 
          <span>{children || text}</span>
        </span>
    </button>
  );
};

// Define prop types
Button.propTypes = {
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  children: PropTypes.node,
  text: PropTypes.string,
  size: PropTypes.oneOf(['sm', 'lg', 'xl']),
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'warning', 'success']),
  outline: PropTypes.bool,
  onClick: PropTypes.func,
  loading: PropTypes.bool, // new prop for loading state
};

export default Button;
