import React from 'react';
import PropTypes from 'prop-types';
import './Input.css';

const Input = ({ label, placeholder, className, type, style, onClick, ...props }) => {
    return (
        <>
            <input
                type={type}
                className={`${className}`} // Added form-control class for Bootstrap styling
                placeholder={placeholder}
                style={style} // Add custom styles
                onClick={onClick} // Click event handler
                {...props} // Spread operator to handle additional props
            />
            {label && <label htmlFor="floatingInput">{label}</label>}
        </>
    );
};

// Prop Types for validation
Input.propTypes = {
    label: PropTypes.string.isRequired,  // Label text
    placeholder: PropTypes.string,  // Placeholder text
    className: PropTypes.string,  // CSS class for styling
    type: PropTypes.string.isRequired,  // Input type (e.g., text, password)
    style: PropTypes.object,  // Custom styles for the input
    onClick: PropTypes.func,  // onClick handler for the input
};

Input.default = {
    placeholder: '',
    className: '',
    style: {},
    onClick: () => {},
};

export default Input;
