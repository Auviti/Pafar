import { useState } from "react";
import PropTypes from "prop-types";
import './Input.css';
const Select = ({ id,label,items=[], currentIndex=0, onChange,className, ...props }) => {
    const [currentIndexState, setCurrentIndexState] = useState(currentIndex);

    
    const handleCurrentIndex = (event) => {
        const index = event.target.value;
        // console.log(index,'===',currentIndexState)
        setCurrentIndexState(index);
        if (onChange) {
            onChange(index); // Call the onCurrentIndex callback if provided
        }
    };
    return (
        
        <>
            <select 
                className={`${className?className:''}`}
                value={currentIndexState} 
                onChange={handleCurrentIndex} // Use onChange here
                {...props} // Spread additional props here
            >
                {items.map((item, index) => (
                    <option 
                        key={index} 
                        value={index} 
                        // onClick={(e, index) => handleCurrentIndex(index)}
                    >
                        {item.label?item.label : item}
                    </option>
                ))}
            </select>
            {label && <label htmlFor="floatingInput" className={`label`} for={id}>{label}</label>}
        </>
    );
};

Select.propTypes = {
    items: PropTypes.arrayOf(PropTypes.string).isRequired,  // Array of strings
    currentIndex: PropTypes.number,  // Optional number
    onCurrentIndex: PropTypes.func,  // Optional callback function
};

Select.default = {
    items:[],
    currentIndex: 0,  // Default to the first option if currentIndex is not provided
};

export default Select;
