import React from 'react';
import PropTypes from 'prop-types'; // Add PropTypes for type checking
import './NavLink.css';
import Badge from '../../Badge/Badge';
import { Link } from 'react-router-dom';

const NavLink = ({ to,children,isMobile, className = '', active = false, onClick,badgeContent, ...props }) => {
    const linkClass = active ? 'navlink navlink-active' : 'navlink'; // Add 'active' class if active is true

    return (
        <Link 
            to={to}
            className={`${linkClass} ${className}  d-flex align-items-center`} // Combine 'active' with any additional className passed
            onClick={onClick} // Optionally handle click events
            {...props}
        >
            {children}
            {/* Render badge if badgeContent is provided */}
            {badgeContent && (
                <Badge isDot={isMobile} >{badgeContent}</Badge>
            )}
        </Link>
    );
};

// PropTypes for better validation
NavLink.propTypes = {
    children: PropTypes.node.isRequired, // Ensures that children are passed
    className: PropTypes.string, // Allows for custom CSS classes
    active: PropTypes.bool, // Boolean to mark the link as active
    onClick: PropTypes.func, // Optional function for handling click events
};

export default NavLink;
