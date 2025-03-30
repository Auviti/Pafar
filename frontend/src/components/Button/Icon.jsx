

import React from 'react';
import PropTypes from 'prop-types';
import Button from './Button';

const IconButton = ({ 
  type = 'button', 
  className,
  children, 
  text, 
  size = 'lg', 
  variant = 'primary', 
  outline, 
  rotate=0,
  onClick, 
  round=true,
  style={},
  ...props 
}) => {
  return (
    
    <Button type={type}
        className={`btn ${round?`btn-round btn-round-sm`:''} ${outline ? `btn-outline-${variant}` : `btn-${variant}`} btn-${size} ${className}`} 
        style={{...style, transform: `rotate(${rotate}deg)` }} // Apply rotation style
        onClick={onClick} 
        {...props}>
        {/* Render Icon if icon prop is provided */}
        {children || text}
    </Button>
  );
};

// Define prop types
IconButton.propTypes = {
  type: PropTypes.oneOf(['button', 'submit', 'reset']),
  children: PropTypes.node,
  text: PropTypes.string,
  size: PropTypes.oneOf(['sm', 'lg', 'xl']),
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'warning', 'success']),
  outline: PropTypes.bool,
  onClick: PropTypes.func,
  rotate: PropTypes.number,
};

export default IconButton;
