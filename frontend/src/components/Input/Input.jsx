import React from 'react';
import PropTypes from 'prop-types';
import './Input.css';

const Input = ({ id,forId,label,value, placeholder, className, type, style, onClick, ...props }) => {
    return (
        <>
            <input
                id={id}
                type={type}
                value={value}
                className={`${className?className:''}`} // Added form-control class for Bootstrap styling
                placeholder={placeholder}
                style={style} // Add custom styles
                onClick={onClick} // Click event handler
                {...props} // Spread operator to handle additional props
            />
            {label && <label htmlFor="floatingInput" className={`label`} for={forId}>{label}</label>}
        </>
    );
};

// Prop Types for validation
Input.propTypes = {
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,  // Label text
    value: PropTypes.any,
    placeholder: PropTypes.string,  // Placeholder text
    className: PropTypes.string,  // CSS class for styling
    type: PropTypes.string.isRequired,  // Input type (e.g., text, password)
    style: PropTypes.object,  // Custom styles for the input
    onClick: PropTypes.func,  // onClick handler for the input
};

Input.default = {
    placeholder: '',
    value:null,
    className: '',
    style: {},
    onClick: () => {},
};

export default Input;
