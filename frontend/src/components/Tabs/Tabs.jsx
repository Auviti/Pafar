import { useState } from "react";
import PropTypes from "prop-types"; // Import PropTypes
import './Tabs.css';
const Tabs = ({ items = [], value = 0, onChangeIndex, onChangeItem }) => {
    const [currentIndex, setCurrentIndex] = useState(value);
    const [currentItem, setCurrentItem] = useState(items.length > 0 ? items[currentIndex] : null);

    const handleTabChange = (index, item) => {
        if (!item.disabled) {
            setCurrentIndex(index);
            setCurrentItem(item);

            // Notify parent component about the tab change
            if (onChangeIndex) onChangeIndex(index);
            if (onChangeItem) onChangeItem(item);
        }
    };

    return (
        <div className="p-3 p-md-4 bg-transparent">
            <ul className="nav nav-tabs">
                {items.map((item, index) => (
                    <li className="nav-item" key={index}>
                        <a
                            className={`nav-link ${currentIndex === index ? 'active' : ''} ${item.disabled ? 'disabled' : ''}`}
                            aria-current="page"
                            href="javascript:void(0)"
                            onClick={() => handleTabChange(index, item)} // Use the handleTabChange function
                        >
                            {item.title}
                        </a>
                    </li>
                ))}
            </ul>
            <div className="p-2">
                {currentItem?.content}
            </div>
        </div>
    );
};

// Adding PropTypes to validate props
Tabs.propTypes = {
    items: PropTypes.arrayOf(
        PropTypes.shape({
            title: PropTypes.string.isRequired,
            content: PropTypes.node.isRequired,
            disabled: PropTypes.bool,
        })
    ).isRequired,
    value: PropTypes.number,
    onChangeIndex: PropTypes.func, // Optional callback for when the index changes
    onChangeItem: PropTypes.func,  // Optional callback for when the item changes
};

Tabs.defaultProps = {
    value: 0, // Default value for the selected tab
};

export default Tabs;
