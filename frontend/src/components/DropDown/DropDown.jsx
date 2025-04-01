import React, { useState, useEffect } from 'react';
import './DropDown.css';
import { Link } from 'react-router-dom';
import Avatar from '../Avatar/Avatar';

const DropDown = ({
  clickItem,
  show = false,
  menuitems = [],
  separator = [],
  userDetails,
  customClass = '',
  onItemClick = () => {},
  itemRenderer = null,
  defaultLinkPrefix = '/accounts',
}) => {
  const [isActive, setIsActive] = useState(show);

  // Close the dropdown when clicking outside of it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.dropdown')) {
        setIsActive(false);
      }
    };

    document.addEventListener('click', handleClickOutside);

    // Clean up the event listener when the component unmounts
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  const handleToggleDropdown = () => {
    setIsActive(!isActive);
  };

  const handleItemClick = (item) => {
    onItemClick(item); // Calling custom click handler if provided
    setIsActive(false); // Close the dropdown on item click
  };

  const defaultItemRenderer = (item, index) => (
    <Link
      key={index}
      className="dropdown-item"
      to={`${defaultLinkPrefix}${userDetails?`/${userDetails.id}`:'/'}${item.link}`}
      state={{ user: userDetails }}
      onClick={() => handleItemClick(item)}
    >
      {item.icon && <Avatar  shape='circle' src={item.icon} alt={item.name}/>}
      {item.name}
    </Link>
  );

  return (
    <div
      className={`dropdown ${isActive ? 'dropdown-active' : ''} ${customClass}`}
      onClick={handleToggleDropdown} // Toggle on click
    >
      {clickItem}

      <div className="dropdown-menu" aria-labelledby="dropdownMenuLink">
        {/* Dynamically render menu items */}
        {menuitems.map((item, index) => (
          <React.Fragment key={index}>
            {/* Render item with custom or default renderer */}
            {itemRenderer ? itemRenderer(item, index) : defaultItemRenderer(item, index)}

            {/* Insert a separator if the index is in the separator array */}
            {separator.includes(index) && <div className="dropdown-divider"></div>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default DropDown;
