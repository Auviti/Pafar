import React from 'react';
import PropTypes from 'prop-types'; // Add PropTypes for type checking
import './NavLink.css';
import Badge from '../../Badge/Badge';
import { Link, useNavigate } from 'react-router-dom'; // Import useNavigate

const NavLink = ({ to, children, isMobile, className = '', active = false, onClick, badgeContent, ...props }) => {
    const linkClass = active ? 'navlink navlink-active' : 'navlink'; // Add 'active' class if active is true
    const navigate = useNavigate(); // For programmatic navigation

    const scrollToSection = (sectionId) => {
        document.getElementById(sectionId).scrollIntoView({
            behavior: 'smooth',
            block: 'start',
        });
    };

    const handleClick = () => {
        if (to.startsWith('#')) {
            const currentUrl = window.location.hash;
            // If current URL is not '/', navigate to '/' first
            if (currentUrl !== '#/') {
                navigate('/'); // Navigate to the root URL
                // Wait for the navigation to complete before scrolling
                setTimeout(() => scrollToSection(to.split('#')[1]), 100); // Scroll after a small delay
            } else {
                // If we're already at '/', just scroll to the section
                scrollToSection(to.split('#')[1]);
            }
        } else {
            // If it's not an anchor link, simply call onClick (if provided)
            if (onClick) onClick();
        }
    };

    if (to.startsWith('#')) {
        return (
            <a
                href="javascript:void(0)"
                className={`${linkClass} ${className} d-flex align-items-center`} // Combine 'active' with any additional className passed
                onClick={handleClick} // Handle the click event to navigate and scroll
                {...props}
            >
                {children}
                {/* Render badge if badgeContent is provided */}
                {badgeContent && <Badge isDot={isMobile}>{badgeContent}</Badge>}
            </a>
        );
    } else {
        return (
            <Link
                to={to}
                className={`${linkClass} ${className} d-flex align-items-center`} // Combine 'active' with any additional className passed
                onClick={onClick} // Optionally handle click events
                {...props}
            >
                {children}
                {/* Render badge if badgeContent is provided */}
                {badgeContent && <Badge isDot={isMobile}>{badgeContent}</Badge>}
            </Link>
        );
    }
};

// PropTypes for better validation
NavLink.propTypes = {
    children: PropTypes.node.isRequired, // Ensures that children are passed
    className: PropTypes.string, // Allows for custom CSS classes
    active: PropTypes.bool, // Boolean to mark the link as active
    onClick: PropTypes.func, // Optional function for handling click events
    to: PropTypes.string.isRequired, // URL or section ID
    badgeContent: PropTypes.node, // Content to display in the badge
    isMobile: PropTypes.bool, // Whether the device is mobile
};

export default NavLink;
