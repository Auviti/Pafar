import React, { useState } from 'react';
import reactLogo from '../../../assets/react.svg';
import NavLink from '../../Links/NavLink/NavLink';
import { Icon } from "@iconify/react";
import Avatar from '../../Avatar/Avatar';

const Bottom = ({ isMobile, navlinks = [], onActiveLink }) => {
    // Step 1: Track the active link index
    const [activeIndex, setActiveIndex] = useState(0);

    // Step 2: Handle click to change active link
    const handleLinkClick = (index,link) => {
        setActiveIndex(index); // Set the clicked link as active
        if (onActiveLink){
            onActiveLink({'activeIndex':activeIndex,'link':link})
        }
    };

    return (
        <nav className="navbar fixed-bottom navbar-expand-lg bg-body-tertiary border-bottom">
            {isMobile && (
                <div className="container-fluid d-flex justify-content-between gap-2">
                    {/* Render navlinks */}
                    {navlinks.map((link, index) => (
                        <NavLink
                            key={index}
                            active={activeIndex === index} // Check if this link is active
                            onClick={() => handleLinkClick(index,link)} // Set active link on click
                            badgeContent={link?.badgeContent}
                            isMobile={isMobile}
                        >
                            {link?.icon}
                        </NavLink>
                    ))}
                </div>
            )}
        </nav>
    );
};

export default Bottom;
