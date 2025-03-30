import { useState } from "react";
import PropTypes from "prop-types";
import './Select.css';

const Select = ({ items, currentIndex=0, onChange, ...props }) => {
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
        <select 
            className="form-select ms-2" 
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
                    {item}
                </option>
            ))}
        </select>
    );
};

Select.propTypes = {
    items: PropTypes.arrayOf(PropTypes.string).isRequired,  // Array of strings
    currentIndex: PropTypes.number,  // Optional number
    onCurrentIndex: PropTypes.func,  // Optional callback function
};

Select.defaultProps = {
    currentIndex: 0,  // Default to the first option if currentIndex is not provided
};

export default Select;
