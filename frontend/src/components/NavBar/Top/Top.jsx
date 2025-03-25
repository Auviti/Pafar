import React, { useState } from 'react';
import reactLogo from '../../../assets/react.svg';
import NavLink from '../../Links/NavLink/NavLink';
import { Icon } from "@iconify/react";
import Avatar from '../../Avatar/Avatar';
import Badge from '../../Badge/Badge';

const Top = ({ isMobile, navlinks = [], onActiveLink }) => {
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
        <nav className="navbar fixed-top navbar-expand-lg bg-body-tertiary border-bottom">
            <div className="container-fluid d-flex justify-content-between">
                <a className="navbar-brand" href="#">
                    <img
                        src={reactLogo}
                        alt="Logo"
                        width="24"
                        height="24"
                        className="d-inline-block align-text-top mx-2"
                    />
                    Bootstrap
                </a>

                {!isMobile && (
                    <div className="d-flex justify-content-between gap-3">
                        {/* Render navlinks */}
                        {navlinks.map((link, index) => (
                            <NavLink
                                key={index}
                                active={activeIndex === index} // Check if this link is active
                                onClick={() => handleLinkClick(index,link)} // Set active link on click
                                badgeContent={link.badgeContent}
                            >
                                {link.name}
                            </NavLink>
                        ))}
                    </div>
                )}

                    <div className="d-flex justify-content-between gap-3">
                        {/* Render navlinks */}
                        <span className='d-flex align-items-center'>
                            <Icon icon="mynaui:search" width="24" height="24" />
                        </span>
                        <span className='d-flex align-items-center'>
                            <Icon icon="lets-icons:bell-light" width="24" height="24" style={{strokeWidth:1.5}}  />
                            <Badge isDot={true} background="primary" /> 
                        </span>

                        
                        <Avatar  shape='circle'/>
                    </div>
            </div>
        </nav>
    );
};

export default Top;
