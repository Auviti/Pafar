import React, { useState, useEffect, useMemo  } from 'react';
import Router from './routes/router';  // Import the Router component that handles the app's routing
import reactLogo from './assets/react.svg'
import travelBg from './assets/pafar-bg.jpeg'
import NewsLetterBg from './assets/newsletter-bg.jpg'
import AbujaBg from './assets/abuja-img.jpg'
import LagosBg from './assets/lagos-img.avif'
import viteLogo from '/vite.svg'
import { Icon } from '@iconify/react';
import './App.css'

import { WebSocketService } from './utils/webSockets';  // Import the WebSocketService
import ThemeProvider from './utils/ThemeProvider'; // Import the ThemeProvider component
import Top from './components/NavBar/Top/Top';
import Bottom from './components/NavBar/Bottom/Bottom';
import Avatar from './components/Avatar/Avatar';
import Button from './components/Button/Button';
import useDeviceType from './hooks/useDeviceType';
import {FormCheckBox, FormInput, FormRadioButton, } from './components/Form/FormInput';
import IconButton from './components/Button/Icon';
import Badge from './components/Badge/Badge';
import Input from './components/Input/Input';
import Footer from './components/Footer/Footer';
import Pagination from './components/Pagination/Pagination';
import Login from './components/Auth/Login';
import Tabs from './components/Tabs/Tabs';

function Home({}) {
  const [count, setCount] = useState(0)
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const {isMobile, isTablet, isDesktop} = useDeviceType();
  const { isLoggedIn, user } = { isLoggedIn: true, user: {} };
  
  // Memoize the socket object so it's only created once and doesn't change on every render
  const socket = useMemo(() => new WebSocketService("ws://localhost:8000"), []);

  useEffect(() => {
    socket.connect((message) => {
      setMessages((prevMessages) => [...prevMessages, message]);
    });
    
    // Cleanup when the component unmounts (important to avoid memory leaks)
    return () => {
      socket.socket.close();
    };
  }, [socket]); // Dependency array with 'socket'

  const handleSendMessage = () => {
    socket.sendMessage(newMessage);
    setNewMessage('');
  };
  
  
  const navlinks = [
    { name: 'Home', icon:<Icon icon='mdi:home' width={24} height={24} />, active: true, onClick: () => alert('Home clicked')},
    { name: 'Places', icon:<Icon icon='mdi:map-marker-outline' width={24} height={24} />, active: false, onClick: () => alert('About clicked'),badgeContent: 'New'  },
    { name: 'Faqs', icon:<Icon icon="mdi:frequently-asked-questions" width={24} height={24} />, active: false, onClick: () => alert('faqs clicked') },
    { name: 'About', icon:<Icon icon='mdi:information' width={24} height={24} />, active: false, onClick: () => alert('About clicked') },
    { name: 'Contact Us', icon:<Icon icon='mdi:phone' width={24} height={24} />, active: false, onClick: () => alert('Contact clicked') },
  ];
  const [selectedIndex, setSelectedIndex] = useState(0);
    const [selectedItem, setSelectedItem] = useState(null);

    const handleIndexChange = (index) => {
        console.log("Selected tab index:", index);
        setSelectedIndex(index);
    };

    const handleItemChange = (item) => {
        console.log("Selected tab item:", item);
        setSelectedItem(item);
    };
  const tabs = [
      { title: "Rent a bus", content: <div>Content 1</div> },
      { title: "Reserve a seat", content: <div>Content 3</div> },
      { title: "Reservation status", content: <div>Content 4</div> },
      // { title: "Tab 3", content: <div>Content 5</div> },
  ];
  const destinations = [
    { name: "Zuma Rock", location: "FCT", city: "Abuja", rating: "4.5", imageUrl: AbujaBg },
    { name: "Olumo Rock", location: "Abeokuta", city: "Ogun", rating: "4.7", imageUrl: travelBg },
    { name: "Erin Ijesha Waterfall", location: "Osun", city: "Osun", rating: "4.6", imageUrl: travelBg },
    { name: "Sukur Cultural Landscape", location: "Adamawa", city: "Adamawa", rating: "4.8", imageUrl: travelBg },
    { name: "Ogbunike Caves", location: "Anambra", city: "Anambra", rating: "4.4", imageUrl: travelBg },
    { name: "Lekki Conservation Centre", location: "Lagos", city: "Lekki", rating: "4.5", imageUrl: LagosBg },
    { name: "Badagry", location: "Lagos", city: "Badagry", rating: "4.3", imageUrl: travelBg },
    { name: "Ngorongoro Crater", location: "Cross River", city: "Calabar", rating: "4.6", imageUrl: travelBg },
    { name: "Yankari National Park", location: "Bauchi", city: "Bauchi", rating: "4.7", imageUrl: travelBg },
  ];
  // <Router API_URL={config.apiUrl} basename={"/web-frontend"}  Companyname={'Oahse'} />
  return (
    <ThemeProvider>
      <Top navlinks={navlinks} isMobile={isMobile}/>
      <div className="container-fluid" style={{height:'50px'}}></div>
        <div className="container px-4 py-5" style={{ backgroundImage: `url(${travelBg})`, backgroundSize: 'cover', backgroundPosition: 'center', borderRadius: '8px' }}>
          <div className="row align-items-center g-lg-3 py-4">
            <div className="col-lg-7 text-center text-lg-start text-white">
              <h1 className="display-4 fw-bold lh-1 mb-3">Revolutionizing Urban Mobility</h1>
              <p className="col-lg-10 fs-7">Pafar is an innovative, technology-driven company committed to reshaping the way people commute across cities in Africa. With our cutting-edge platform, we offer a seamless and efficient travel experience that empowers commuters, making transportation simpler, safer, and more reliable.</p>
            </div>
            <div className="col-md-10 mx-auto rounded-3 col-lg-5" style={{backgroundColor: 'rgba(141, 140, 140, 0.5)', borderColor:'rgba(141, 140, 140)'}}>
              {isLoggedIn?
              <Tabs
                  items={tabs}
                  value={selectedIndex}
                  onChangeIndex={handleIndexChange}
                  onChangeItem={handleItemChange}
              />
              :
              <Login />
              }
              
              
            </div>
          </div>
        </div>
        <div className="container-fluid" style={{height:'20px'}}></div>
        <div className='p-2'>
          <div className="container px-5 py-2" style={{backgroundColor: 'rgba(141, 140, 140, 0.5)', borderColor:'rgba(141, 140, 140)', borderRadius: '8px' }}>
            <div className='row align-items-center my-2'>
              <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-dark p-1" style={{ borderRight: '1px solid #fff',...(!isDesktop && { borderBottom: '1px solid #fff' }) }}>
                <span className='d-flex justify-content-start align-items-center'>
                    <h3>1</h3> <span className='ms-2'>Trans Modes</span>
                </span>
              </div>

              <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-dark p-1" style={{ ...(!isMobile && { borderRight: '1px solid #fff' }),...(!isDesktop && { borderBottom: '1px solid #fff' })  }}>
                <span className='d-flex justify-content-start align-items-center'>
                    <h3>54k</h3> <span className='ms-2'>ADPs</span>
                </span>
              </div>
              <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-dark p-1" style={{ ...(!isTablet && { borderRight: '1px solid #fff' }),...(isTablet && { borderBottom: '1px solid #fff' })  }}>
                <span className='d-flex justify-content-start align-items-center'>
                  <h3 >54</h3> <span className='ms-2'>Branches</span>
                </span>
              </div>

              <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start p-1" style={{ ...(isTablet && { borderRight: '1px solid #fff' }) }}>
                <Button className="w-100" size='lg' variant='primary' type="submit" >Sign up</Button>
              </div>
            </div>
          </div>
        </div>
        <div className="container mx-auto py-2" style={{borderRadius: '8px' }}>
          <h3 className='text-center border-bottom pb-3 pt-4'>Top 9 Popular Destinations</h3>
          
          <div className='row align-items-center'>
            {destinations.map((destination, index) => (
              <div key={index} className="col-lg-4 col-md-6 col-12 my-4">
                <div className="p-0 shadow-lg mx-auto" style={{ width: '18rem', height: '14rem', borderColor: 'rgba(141, 140, 140)', borderRadius: '10px' }}>
                  <div
                    style={{
                      height: '100%',
                      backgroundImage: `url(${destination.imageUrl})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                      borderRadius: '10px',
                      position: 'relative',
                    }}
                  >
                    <div className="card-info" style={{ position: 'absolute', bottom: '10px', left: '10px', color: 'white' }}>
                      <div className='d-flex justify-content-between'>
                        <div style={{ lineHeight: 1 }}>
                          <small>{destination.location}</small>
                          <br />
                          <small style={{ fontSize: '10px', lineHeight: 0 }}>
                            {destination.city} <span className='ms-2'>{destination.rating} ⭐</span>
                          </small>
                        </div>

                        <div>
                          <IconButton variant='primary' outline rotate={45}>
                            <svg xmlns="http://www.w3.org/2000/svg" width={21} height={21} viewBox="0 0 21 21">
                              <path fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" d="m14.5 7.5l-4-4l-4.029 4m4.029-4v13" strokeWidth={1}></path>
                            </svg>
                          </IconButton>

                          <IconButton className='ms-1' variant='primary' outline>
                            <Icon icon="mdi-light:bookmark" width="21" height="21" />
                          </IconButton>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

            ))}
          </div>
        </div>
        <div className="container mx-auto py-2" style={{borderRadius: '8px' }}>
          <div className='d-flex justify-content-between align-items-center border-bottom'>
                        <span>
                          
                        </span>
                        <div>
                          <h3 className='text-center pb-3 pt-4'>What Our Clients say</h3>
                        </div>
                        <span>
                          
                        </span>
                        
                      </div>
                      
          <div className='row align-items-center'>
            
            {[1,2,3,4].map((user, index)=>(
              <div key={index} className="col-lg-3 col-md-4 col-12 my-2">
                <div className="shadow-lg mx-auto" style={{ minWidth: '9rem', height: '9rem', borderRadius: '10px' }}>
                  <div
                    style={{
                      height: '100%',
                      borderRadius: '10px', // Ensures the image has the same border-radius as the container
                      position: 'relative', // To make sure the inner content can be placed above the image
                    }}
                    className='border'
                  >
                    <div className='card-body-small truncate'>
                        "Booking with Stay Sary was a breeze. I found a beautiful hotel in Brighton at a great price. The entire process was smooth, and the
                        customer support was excellent!"
                    </div>
                    <div
                      className="card-info-small mx-auto"
                      
                    >
                      <div className="row align-items-center">
                        {/* Avatar Column (1 part) */}
                        <div className="col-2">
                          <Avatar shape="circle" src={user.picture||null} />
                        </div>

                        {/* Text Column (3 parts) */}
                        <div className="col d-flex flex-column px-1">
                          <div style={{ lineHeight: 1 }}>
                            <small>{user.picture||'David John'}</small>
                            <br />
                            <small style={{ fontSize: '10px', lineHeight: 0 }}>oct 15 2024</small>
                          </div>
                        </div>

                        {/* Badge Column (1 part) */}
                        <div className="col-lg-4 col-md-4 col-3">
                            <Badge badgeContent={'4/5 ⭐'} background="transparent" color={'black'} />
                        </div>
                      </div>

                    </div>
                  </div>
                </div>
              </div>
            ))}

          </div>
          <div className='d-flex justify-content-between align-items-center'>
                        <span>
                          
                        </span>
                        <span>
                          
                        </span>
                        <Pagination items={[1,2,3,4,5,6,7]} showranges/>
                      </div>
          </div>
          <div class="container px-4 py-5">
            <h2 class="pb-2 border-bottom">Make a Booking</h2>

            <div class="row row-cols-1 row-cols-md-2 align-items-md-center g-5 py-5">
              <div class="col d-flex flex-column align-items-start gap-2">
                <h2 class="fw-bold text-body-emphasis">Explore Our Premium Booking Features</h2>
                <p class="text-body-secondary">Discover the ease of booking your next trip with us. Whether you're looking for luxury, comfort, or convenience, we have something tailored to your needs. Our seamless process ensures you'll have a stress-free booking experience from start to finish.</p>
                {/* <!-- <a href="#" class="btn btn-primary btn-lg">Primary button</a> --> */}
                <Button>Start Your Booking</Button>
              </div>

              <div class="col">
                <div class="row row-cols-1 row-cols-sm-2 g-4">
                  <div class="col d-flex flex-column gap-2 cursor-pointer">
                    <div class="feature-icon-small d-inline-flex align-items-center justify-content-center bg-primary bg-gradient fs-4 rounded-3 p-2" style={{width:'64px'}}>
                        <svg xmlns="http://www.w3.org/2000/svg" width={34} height={34} viewBox="0 0 24 24">
                          <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} color="currentColor">
                            <path d="M14.5 9a2.5 2.5 0 1 1-5 0a2.5 2.5 0 0 1 5 0"></path>
                            <path d="M13.257 17.494a1.813 1.813 0 0 1-2.514 0c-3.089-2.993-7.228-6.336-5.21-11.19C6.626 3.679 9.246 2 12 2s5.375 1.68 6.467 4.304c2.016 4.847-2.113 8.207-5.21 11.19M18 20c0 1.105-2.686 2-6 2s-6-.895-6-2">

                            </path>
                          </g>
                        </svg>
                    </div>
                    <h4 class="fw-semibold mb-0 text-body-emphasis">Wide Selection of Destinations</h4>
                    <p class="text-body-secondary">Choose from a diverse range of destinations around the world, from beach resorts to mountain escapes.</p>
                  </div>

                  <div class="col d-flex flex-column gap-2 cursor-pointer">
                    <div class="feature-icon-small d-inline-flex align-items-center justify-content-center bg-primary bg-gradient fs-4 rounded-3 p-2" style={{width:'64px'}}>
                      <svg xmlns="http://www.w3.org/2000/svg" width={34} height={34} viewBox="0 0 14 14">
                      <g fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth={0.5}>
                        <path d="M6.35.5h6.302c.469 0 .849.38.849.849v6.778c0 .47-.38.85-.849.85H7.5M3.149 4.001a1.75 1.75 0 1 0 0-3.501a1.75 1.75 0 0 0 0 3.501"></path><path d="M9 5.527C9 4.96 8.54 4.5 7.973 4.5H3.149v0A2.65 2.65 0 0 0 .5 7.149V9.5h1.135l.379 4h2.27l.872-6.945h2.817C8.54 6.555 9 6.095 9 5.527">
                        </path></g></svg>
                      </div>
                    <h4 class="fw-semibold mb-0 text-body-emphasis">Choose Your Travel Class</h4>
                    <p class="text-body-secondary">Select the travel class that fits your preferences – from economy to VIP and business options.</p>
                  </div>

                  <div class="col d-flex flex-column gap-2 cursor-pointer">
                    <div class="feature-icon-small d-inline-flex align-items-center justify-content-center bg-primary bg-gradient fs-4 rounded-3 p-2" style={{width:'64px'}}>
                    <svg xmlns="http://www.w3.org/2000/svg" width={34} height={34} viewBox="0 0 20 20">
                    <path fill="currentColor" d="M9 4a.5.5 0 0 0 0 1h2a.5.5 0 0 0 0-1zm-1 9a1 1 0 1 1-2 0a1 1 0 0 1 2 0m5 1a1 1 0 1 0 0-2a1 1 0 0 0 0 2M3 5.5A3.5 3.5 0 0 1 6.5 2h7A3.5 3.5 0 0 1 17 5.5V8h1a.5.5 0 0 1 0 1h-1v7.5a1.5 1.5 0 0 1-1.5 1.5h-1a1.5 1.5 0 0 1-1.5-1.5V16H7v.5A1.5 1.5 0 0 1 5.5 18h-1A1.5 1.5 0 0 1 3 16.5V9H2a.5.5 0 0 1 0-1h1zm13 0A2.5 2.5 0 0 0 13.5 3h-7A2.5 2.5 0 0 0 4 5.5V10h12zM14 16v.5a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5V16zM4 16v.5a.5.5 0 0 0 .5.5h1a.5.5 0 0 0 .5-.5V16zm0-1h12v-4H4z">
                      </path></svg>
                    </div>
                    <h4 class="fw-semibold mb-0 text-body-emphasis">Select Your Vehicle</h4>
                    <p class="text-body-secondary">Choose from a range of vehicles for your journey – whether it's a sedan, SUV, or luxury car.</p>
                  </div>

                  <div class="col d-flex flex-column gap-2 cursor-pointer">
                    <div class="feature-icon-small d-inline-flex align-items-center justify-content-center bg-primary bg-gradient fs-4 rounded-3 p-2" style={{width:'64px'}}>
                    <svg xmlns="http://www.w3.org/2000/svg" width={34} height={34} viewBox="0 0 1024 1024">
                    <path fill="currentColor" d="m960 95.888l-256.224.001V32.113c0-17.68-14.32-32-32-32s-32 14.32-32 32v63.76h-256v-63.76c0-17.68-14.32-32-32-32s-32 14.32-32 32v63.76H64c-35.344 0-64 28.656-64 64v800c0 35.343 28.656 64 64 64h896c35.344 0 64-28.657 64-64v-800c0-35.329-28.656-63.985-64-63.985m0 863.985H64v-800h255.776v32.24c0 17.679 14.32 32 32 32s32-14.321 32-32v-32.224h256v32.24c0 17.68 14.32 32 32 32s32-14.32 32-32v-32.24H960zM736 511.888h64c17.664 0 32-14.336 32-32v-64c0-17.664-14.336-32-32-32h-64c-17.664 0-32 14.336-32 32v64c0 17.664 14.336 32 32 32m0 255.984h64c17.664 0 32-14.32 32-32v-64c0-17.664-14.336-32-32-32h-64c-17.664 0-32 14.336-32 32v64c0 17.696 14.336 32 32 32m-192-128h-64c-17.664 0-32 14.336-32 32v64c0 17.68 14.336 32 32 32h64c17.664 0 32-14.32 32-32v-64c0-17.648-14.336-32-32-32m0-255.984h-64c-17.664 0-32 14.336-32 32v64c0 17.664 14.336 32 32 32h64c17.664 0 32-14.336 32-32v-64c0-17.68-14.336-32-32-32m-256 0h-64c-17.664 0-32 14.336-32 32v64c0 17.664 14.336 32 32 32h64c17.664 0 32-14.336 32-32v-64c0-17.68-14.336-32-32-32m0 255.984h-64c-17.664 0-32 14.336-32 32v64c0 17.68 14.336 32 32 32h64c17.664 0 32-14.32 32-32v-64c0-17.648-14.336-32-32-32" strokeWidth={0.1} stroke="currentColor">
                      </path></svg>
                    </div>
                    <h4 class="fw-semibold mb-0 text-body-emphasis">Pick a Date That Works for You</h4>
                    <p class="text-body-secondary">Select the date that fits your schedule – we offer flexibility for all types of trips.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="container my-3" style={{ backgroundImage: `url(${NewsLetterBg})`, backgroundSize: 'cover', backgroundPosition: 'center'}}>
            <div class="p-5 text-center text-white bg-transparent rounded-3" >
              <h1 class="text-body-white">Contact Us</h1>
              <p class="col-lg-8 mx-auto fs-5 text-muted">
                For any inquiries
              </p>
              <Button size='lg' variant='primary' type="submit" >Contact Us</Button>
            </div>
          </div>
          
      <Footer/>
      <Bottom navlinks={navlinks} isMobile={isMobile}/>
    </ThemeProvider>
    
  );
}

export default Home;

