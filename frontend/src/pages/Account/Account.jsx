import React, { useState, useEffect } from 'react';
import ThemeProvider from '../../utils/ThemeProvider';
import Button from '../../components/Button/Button';
import Tabs from '../../components/Tabs/Tabs';
import Profile from './Profile';
import { useNavigate } from 'react-router-dom';
import Billings from './Billings';
import Security from './Security';
import Notifications from './Notifications';

const Account = ({ header, footer, index, bottomheader, isLoggedIn, user }) => {
    const navigate = useNavigate();
    
    const [selectedIndex, setSelectedIndex] = useState(index || 0);

    // useEffect to set the initial selected tab based on the current URL
    useEffect(() => {
        const pathname = window.location.pathname;  // Get the current URL path

        // Check the URL path to set the correct tab index
        if (pathname.includes('/profile')) {
            setSelectedIndex(0);
        } else if (pathname.includes('/billing')) {
            setSelectedIndex(1);
        } else if (pathname.includes('/security')) {
            setSelectedIndex(2);
        } else if (pathname.includes('/notifications')) {
            setSelectedIndex(3);
        } else {
            setSelectedIndex(0);  // Default case if no match
        }
    }, []); // The empty dependency array ensures this runs once when the component mounts
    
    // Function to handle tab index changes
    const handleIndexChange = (index) => {
        setSelectedIndex(index);

        // Switch cases for navigation based on the selected index
        switch (index) {
            case 0:
                navigate(`/accounts/${user?.id}/profile`);
                break;
            case 1:
                navigate(`/accounts/${user?.id}/billing`);
                break;
            case 2:
                navigate(`/accounts/${user?.id}/security`);
                break;
            case 3:
                navigate(`/accounts/${user?.id}/notifications`);
                break;
            default:
                navigate(`/accounts/${user?.id}/profile`);
        }
    };

    // Tabs data (titles and contents)
    const tabs = [
        { 
            title: "Profile", 
            content: <Profile user={user} isLoggedIn={isLoggedIn} />
        },
        { 
            title: "Billing", 
            content: <Billings user={user} isLoggedIn={isLoggedIn} />
        },
        { 
            title: "Security", 
            content: <Security user={user} isLoggedIn={isLoggedIn} />
        },
        { 
            title: "Notifications", 
            content: <Notifications user={user} isLoggedIn={isLoggedIn} /> 
        },
    ];

    return (
        <ThemeProvider>
            {header}
            <div className="container-fluid" style={{ height: '50px' }}></div>
            <Tabs
                    items={tabs}
                    value={selectedIndex}
                    onChangeIndex={handleIndexChange}  // Handles tab index change
                />
            {footer}<a className="text-arrow-icon small" href="#!">
                        Switch to yearly billing
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" className="feather feather-arrow-right"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
                    </a>
            {bottomheader}
        </ThemeProvider>
    );
};

export default Account;
