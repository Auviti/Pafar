import React from 'react';
import PropTypes from 'prop-types';
import './Button.css';

const Button = ({ 
  type = 'button', 
  className,
  children, 
  text, 
  size = 'lg', 
  variant = 'primary', 
  outline, 
  onClick, 
  style={},
  ...props 
}) => {
  return (
    <button 
      type={type}
      className={`btn ${outline ? `btn-outline-${variant}` : `btn-${variant}`} btn-${size} ${className}`} 
      style={style}
      onClick={onClick} 
      {...props}
    >
      {children || text}
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
};

export default Button;
