import React from 'react';
import './Button.css';

const Button = ({ children,text, variant = 'primary', outline = false , onClick,...props }) => {
  return (
    <button 
    className={`btn ${outline ? `btn-outline-${variant}` : `btn-${variant}`}`}
      onClick={onClick}
      {...props}
    >
      {children?children:text}
    </button>
  );
};

export default Button;

