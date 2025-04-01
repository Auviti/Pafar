import React, { useState } from 'react';
import Button from "../../components/Button/Button"
import { Link } from 'react-router-dom';
import ThemeProvider from '../../utils/ThemeProvider';

const NotFound = ({onActiveLink,navlinks}) => {
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
        <ThemeProvider>
            <div class="notfound text-dark">
                <div class="d-flex align-items-center justify-content-center min-vh-100 px-2">
                    <div class="text-center">
                        <h1 class="display-1 fw-bold">404</h1>
                        <p class="fs-2 fw-medium mt-4">Oops! Page not found</p>
                        <p class="mt-4 mb-5">The page you're looking for doesn't exist or has been moved.</p>
                        
                        <Link to='/' style={{textDecoration:'none'}} onClick = {() => handleLinkClick(0,navlinks[0])} > <Button> Go Home</Button></Link>
                    </div>
                </div>
            </div>
        </ThemeProvider>
        
    )
}
export default NotFound;