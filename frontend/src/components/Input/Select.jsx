import { useState } from "react";
import PropTypes from "prop-types";
import './Input.css';

const Select = ({ id, label, items = [], currentIndex = 0, onChange, className, ...props }) => {
    const [currentIndexState, setCurrentIndexState] = useState(items[0]?items[0].value:null);

    const handleCurrentIndex = (event) => {
        const value = event.target.value; // Convert string to number
        setCurrentIndexState(value);
        if (onChange) {
            onChange(value);
        }
    };

    return (
        <>
            <select
                id={id}
                className={`${className ? className : ''}`}
                value={currentIndexState}
                onChange={handleCurrentIndex}
                {...props}
            >
                {items.map((item, index) => (
                    <option key={index} value={item.value?item.value:index}>
                        {item.label ? item.label : item}
                    </option>
                ))}
            </select>
            {label && <label htmlFor={id} className="label">{label}</label>}
        </>
    );
};

Select.propTypes = {
    id: PropTypes.string,
    label: PropTypes.string,
    items: PropTypes.arrayOf(
        PropTypes.oneOfType([
            PropTypes.string,
            PropTypes.shape({
                label: PropTypes.string,
                value: PropTypes.any
            })
        ])
    ).isRequired,
    currentIndex: PropTypes.number,
    onChange: PropTypes.func,
    className: PropTypes.string
};

Select.default = {
    items: [],
    currentIndex: 0
};

export default Select;
