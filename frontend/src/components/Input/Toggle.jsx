import React from 'react';
import PropTypes from 'prop-types';
import './Input.css';

const Toggle = ({
    id,
    label,
    value,
    labelClassName,
    className,
    style,
    checked,
    disabled,
    onClick,
    ...props
}) => {
    return (
        <>
            <input 
                id={id}
                type="checkbox" 
                role="switch"
                value={value} 
                className={className} // Added class for styling (you can add 'form-control' class if needed)
                style={style} // Custom styles
                disabled={disabled}
                checked={checked}
                onClick={onClick} // Click event handler
                {...props} // Spread operator to handle additional props
            />
            <label className={labelClassName} htmlFor={id}>{label}</label> {/* Corrected "for" to "htmlFor" */}
        </>
    );
};

// Prop Types for validation
Toggle.propTypes = {
    label: PropTypes.string.isRequired,  // Label text
    id: PropTypes.string.isRequired,  // Unique ID for the input (required)
    className: PropTypes.string,  // CSS class for styling
    style: PropTypes.object,  // Custom styles for the input
    value: PropTypes.string,  // Value of the checkbox (optional)
    checked: PropTypes.bool,  // Whether the checkbox is checked
    disabled: PropTypes.bool,  // Whether the checkbox is disabled
    onClick: PropTypes.func,  // onClick handler for the input
    labelClassName: PropTypes.string,  // CSS class for label
};

// Default prop values
Toggle.defaultProps = {
    className: '',
    style: {},
    value: '',  // Default value is an empty string
    checked: false,  // Default to unchecked
    disabled: false,  // Default to enabled
    onClick: () => {},  // Default empty function for onClick
    labelClassName: '',  // Default to no additional styling for the label
};

export default Toggle;
