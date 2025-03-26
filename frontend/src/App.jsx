import React, { useState, useEffect, useMemo  } from 'react';
import reactLogo from './assets/react.svg'
import travelBg from './assets/pafar-bg.jpeg'
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
function App() {
  const [count, setCount] = useState(0)
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const {isMobile} = useDeviceType();
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
    { name: 'About', icon:<Icon icon='mdi:information' width={24} height={24} />, active: false, onClick: () => alert('About clicked') },
    { name: 'Contact Us', icon:<Icon icon='mdi:phone' width={24} height={24} />, active: false, onClick: () => alert('Contact clicked') },
  ];

  return (
    <ThemeProvider>
      <Top navlinks={navlinks} isMobile={isMobile}/>
      <div className="container-fluid" style={{height:'66px'}}></div>
        <div className="container px-4 py-5" style={{ backgroundImage: `url(${travelBg})`, backgroundSize: 'cover', backgroundPosition: 'center', borderRadius: '8px' }}>
          <div className="row align-items-center g-lg-3 py-4">
            <div className="col-lg-7 text-center text-lg-start text-white">
              <h1 className="display-4 fw-bold lh-1 mb-3">Revolutionizing Urban Mobility</h1>
              <p className="col-lg-10 fs-7">Pafar is an innovative, technology-driven company committed to reshaping the way people commute across cities in Africa. With our cutting-edge platform, we offer a seamless and efficient travel experience that empowers commuters, making transportation simpler, safer, and more reliable.</p>
            </div>
            <div className="col-md-10 mx-auto rounded-3 col-lg-5" style={{backgroundColor: 'rgba(141, 140, 140, 0.5)', borderColor:'rgba(141, 140, 140)'}}>
              <form class="p-4 p-md-5 bg-light">
                <FormInput type="email" label="Email address" placeholder="name@example.com"/>
                <div class="form-floating mb-3">
                  <input type="password" class="form-control" id="floatingPassword" placeholder="Password" />
                  <label for="floatingPassword">Password</label>
                </div>
                <FormCheckBox value="remember-me" label={'Remember me'}/>
                <button class="w-100 btn btn-lg btn-primary" type="submit">Sign up</button>
                <hr class="my-4"/>
                <small class="text-muted">By clicking Sign up, you agree to the terms of use.</small>
              </form>
            </div>
          </div>
        </div>
        <div className="container-fluid" style={{height:'20px'}}></div>
        <div className="container px-5 py-2 " style={{backgroundColor: 'rgba(141, 140, 140, 0.5)', borderColor:'rgba(141, 140, 140)', borderRadius: '8px' }}>
          <div className='row align-items-center m-2'>
            <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-white" style={{ borderRight: '1px solid #fff' }}>
              Column 1
            </div>

            <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-white" style={{ borderRight: '1px solid #fff' }}>
              Column 2
            </div>
            <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-white" style={{ borderRight: '1px solid #fff' }}>
              Column 3
            </div>

            <div className="col-lg-3 col-md-4 col-6 text-center text-lg-start text-white">
              <button className="w-100 btn btn-lg btn-primary" type="submit">Sign up</button>
            </div>
          </div>
        </div>
        <div className="container mx-auto py-2" style={{borderRadius: '8px' }}>
          <span className='d-block text-center my-3'>Top 9 Popular Destinations</span>
          <div className='row align-items-center'>
            
            {[1,2,3,4,5,6,7,8,9].map((destination, index)=>(
              <div key={index} className="col-lg-4 col-md-6 col-12 my-4">
                <div className="p-2 shadow-lg mx-auto" style={{ width: '18rem', height: '14rem', borderRadius: '10px' }}>
                  <div
                    style={{
                      height: '100%',
                      backgroundImage: `url(${travelBg})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                      borderRadius: '10px', // Ensures the image has the same border-radius as the container
                      position: 'relative', // To make sure the inner content can be placed above the image
                    }}
                  >
                    <div
                      className="card-info"
                      style={{
                        
                      }}
                    >
                      <div className='d-flex justify-content-between'>
                        <div>
                          Lagos
                          <br/><small style={{fontSize:'10px'}}>Ikeja <span className='ms-2'>4/5 ⭐</span></small>
                        </div>
                        <span>
                          --d-
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

          </div>
        </div>
        <div className="container mx-auto py-2" style={{borderRadius: '8px' }}>
          <div className='d-flex justify-content-between px-5'>
                        <span>
                          
                        </span>
                        <div>
                          <span className='d-block text-center ms-4'>What Our Clients say</span>
                        </div>
                        <Icon icon='mdi:home' width={24} height={24}/>
                        
                      </div>
          <div className='row align-items-center'>
            
            {[1,2,3,4].map((destination, index)=>(
              <div key={index} className="col-lg-3 col-md-6 col-12 my-4">
                <div className="p-2 shadow-lg mx-auto" style={{ width: '16rem', height: '12rem', borderRadius: '10px' }}>
                  <div
                    style={{
                      height: '100%',
                      backgroundImage: `url(${travelBg})`,
                      backgroundSize: 'cover',
                      backgroundPosition: 'center',
                      borderRadius: '10px', // Ensures the image has the same border-radius as the container
                      position: 'relative', // To make sure the inner content can be placed above the image
                    }}
                  >
                    <div
                      className="card-info card-info-small"
                      
                    >
                      <div className='d-flex justify-content-between'>
                        <div>
                          Lagos
                          <br/><small style={{fontSize:'10px'}}>Ikeja <span className='ms-2'>4/5 ⭐</span></small>
                        </div>
                        <span>
                          --d-
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

          </div>
        </div>
      <div className="container-fluid" style={{height:'70px'}}></div>
      <Bottom navlinks={navlinks} isMobile={isMobile}/>
    </ThemeProvider>
    
  );
}

export default App;

