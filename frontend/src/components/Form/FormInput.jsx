import React from 'react';
import Input from "../Input/Input";
import CheckBox from '../Input/CheckBox';
import RadioButton from '../Input/RadioBox';

const FormInput = ({ id,forId,label,value, placeholder, className, type, style, onClick, ...props }) => {
    return (
        <div className="form-floating">
            <Input
                id={id}
                forId={forId}
                type={type}
                label={label}
                value={value}
                placeholder={placeholder}
                className={`form-control ${className?className:''}`} // Apply form-control class from Bootstrap
                style={style}
                onClick={onClick}
                {...props} // Spread additional props to the Input component
            />
        </div>
    );
};
const FormCheckBox = ({ label, value, className, style,checked, onClick,disabled, ...props }) => {
    return (
        <div className="form-check checkbox">
            <CheckBox
                label={label}
                value={value}
                className={`form-check-input ${className}`} // Apply form-control class from Bootstrap
                style={style}
                checked={checked}
                disabled={disabled}
                onClick={onClick}
                {...props} // Spread additional props to the Input component
            />
        </div>
    );
};
const FormRadioButton = ({ label, value,name, className, style,checked, onClick,disabled, ...props }) => {
    return (
        <div className="form-check checkbox mb-3">
            <RadioButton
                label={label}
                value={value}
                name={name}
                className={`form-check-input ${className}`} // Apply form-control class from Bootstrap
                style={style}
                checked={checked}
                disabled={disabled}
                onClick={onClick}
                {...props} // Spread additional props to the Input component
            />
        </div>
    );
};

export {FormInput,FormCheckBox, FormRadioButton};
