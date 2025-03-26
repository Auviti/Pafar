import React from 'react';
import PropTypes from 'prop-types';
import './Input.css';

const RadioButton = ({ label, value,className, style, disabled, onClick, name, ...props }) => {
    return (
        <label>
            <input 
                type="radio" 
                value={value} 
                className={className} // Added form-control class for Bootstrap styling
                style={style} // Add custom styles
                disabled={disabled}
                onClick={onClick} // Click event handler
                name={name} // Added name to group radio buttons
                {...props} // Spread operator to handle additional props
            /> 
            <span className='ms-2'>{label}</span>
        </label>
    );
};

// Prop Types for validation
RadioButton.propTypes = {
    label: PropTypes.string.isRequired,  // Label text
    value: PropTypes.string.isRequired,  // Value of the radio button
    className: PropTypes.string,  // CSS class for styling
    style: PropTypes.object,  // Custom styles for the input
    onClick: PropTypes.func,  // onClick handler for the input
    name: PropTypes.string.isRequired,  // Name to group the radio buttons
    disabled: PropTypes.bool,  // To disable the radio button
};

// Default Props
RadioButton.defaultProps = {
    className: '',
    style: {},
    onClick: () => {},
    disabled: false,
};

export default RadioButton;
