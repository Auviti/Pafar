import React, { useState, useEffect, useMemo  } from 'react';
import Router from './routes/routes';  // Import the Router component that handles the app's routing

import './App.css'
import Top from './components/NavBar/Top/Top';
import useDeviceType from './hooks/useDeviceType';
import Footer from './components/Footer/Footer';
import Bottom from './components/NavBar/Bottom/Bottom';
import { Icon } from '@iconify/react';
import { useLocation } from 'react-router-dom';
import NotFound from './pages/NotFound/NotFound';

function App({}) {
  const {isMobile, isTablet, isDesktop} = useDeviceType();
  const { isLoggedIn, user } = { isLoggedIn: true, user: {id:'1'} };
  const [currentUrl, setCurrentUrl] = useState('/');
  
  const navlinks = [
      { name: 'Home', link:'/', icon:<Icon icon='mdi:home' width={24} height={24} />, active: true, onClick: () => alert('Home clicked')},
      { name: 'Places', link:'/places', icon:<Icon icon='mdi:map-marker-outline' width={24} height={24} />, active: false, onClick: () => alert('About clicked'),badgeContent: 'New'  },
      { name: 'Faqs', link:'#faqs', icon:<Icon icon="mdi:frequently-asked-questions" width={24} height={24} />, active: false, onClick: () => alert('faqs clicked') },
      { name: 'About', link:'#about', icon:<Icon icon='mdi:information' width={24} height={24} />, active: false, onClick: () => alert('About clicked') },
      { name: 'Contact Us', link:'#contactus', icon:<Icon icon='mdi:phone' width={24} height={24} />, active: false, onClick: () => alert('Contact clicked') },
    ];
  
  useEffect(() => {
    // Get the current pathname and hash from window.location
    const pathname = window.location.pathname;
    const hash = window.location.hash;
  
    // Check the conditions based on pathname or hash and update the currentUrl
    if (pathname.includes('/places') || hash.includes('/places')) {
      setCurrentUrl('/places');
    } else if (pathname.includes('/faqs') || hash.includes('/faqs')) {
      setCurrentUrl('/');
    } else if (pathname.includes('/about') || hash.includes('/about')) {
      setCurrentUrl('/');
    } else if (pathname.includes('/contactus') || hash.includes('/contactus')) {
      setCurrentUrl('/');
    } else if (pathname.includes('/profile') || hash.includes('/profile')) {
      setCurrentUrl('/profile');
    }  else if (pathname.includes('/billing') || hash.includes('/billing')) {
        setCurrentUrl('/billing');
    } else if (pathname.includes('/security') || hash.includes('/security')) {
      setCurrentUrl('/security');
    } else if (pathname.includes('/notifications') || hash.includes('/notifications')) {
      setCurrentUrl('/notifications');
    } else {
      setCurrentUrl('/');  // Default case if no match
    }
  }, [window.location.pathname, window.location.hash]);  // Run effect when pathname or hash changes

  const handleActiveLink=(value)=>{
    // onActiveLink({'activeIndex':activeIndex,'link':link})
    setCurrentUrl(value.link.link)
  }

  return (
    <Router 
      API_URL={'config.apiUrl'} 
      basename={"/"}  
      Companyname={'Pafar'} 
      isLoggedIn={isLoggedIn}
      user={user}
      currentUrl={currentUrl}
      header={<Top navlinks={navlinks} isLoggedIn={isLoggedIn} user={user} isMobile={isMobile} currentUrl={currentUrl} onActiveLink={handleActiveLink}/>}
      footer={<Footer isLoggedIn={isLoggedIn} user={user}/>}
      notfound={<NotFound onActiveLink={handleActiveLink} navlinks={navlinks}/>}
      bottomheader={<Bottom navlinks={navlinks} isLoggedIn={isLoggedIn} user={user} isMobile={isMobile} currentUrl={currentUrl} onActiveLink={handleActiveLink}/>} />

  );
}

export default App;

