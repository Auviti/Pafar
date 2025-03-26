import React from 'react';
import PropTypes from 'prop-types';
import './Input.css';

const CheckBox = ({ label,value, className, style,checked, disabled,onClick, ...props }) => {
    return (
        <label>
            <input 
                type="checkbox" 
                value={value} 
                className={className} // Added form-control class for Bootstrap styling
                style={style} // Add custom styles
                disabled={disabled}
                checked={checked}
                onClick={onClick} // Click event handler
                {...props} // Spread operator to handle additional props
            /> 
            <span className='ms-2'>{label}</span>
        </label>
    );
};

// Prop Types for validation
CheckBox.propTypes = {
    label: PropTypes.string.isRequired,  // Label text
    className: PropTypes.string,  // CSS class for styling
    style: PropTypes.object,  // Custom styles for the input
    onClick: PropTypes.func,  // onClick handler for the input
};

CheckBox.default = {
    className: '',
    style: {},
    onClick: () => {},
};

export default CheckBox;

