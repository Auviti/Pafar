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
import Card from './components/Card/Card';
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
      <div className="container-fluid" style={{height:'66px'}}>
        </div>
        <div class="container px-4 py-5" style={{ backgroundImage: `url(${travelBg})`, backgroundSize: 'cover', backgroundPosition: 'center', borderRadius: '8px' }}>
          <div class="row align-items-center g-lg-3 py-4">
            <div class="col-lg-7 text-center text-lg-start text-white">
              <h1 class="display-4 fw-bold lh-1 mb-3">Revolutionizing Urban Mobility</h1>
              <p class="col-lg-10 fs-7">Pafar is an innovative, technology-driven company committed to reshaping the way people commute across cities in Africa. With our cutting-edge platform, we offer a seamless and efficient travel experience that empowers commuters, making transportation simpler, safer, and more reliable.</p>
            </div>
            <div class="col-md-10 mx-auto col-lg-5">
              <form class="p-4 p-md-5 border rounded-3 bg-light">
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
        {/* <div className="container-fluid">
          
          <header className="App-header">
          <div>
              <a href="https://vite.dev" target="_blank">
                <img src={viteLogo} className="logo" alt="Vite logo" />
              </a>
              <a href="https://react.dev" target="_blank">
                <img src={reactLogo} className="logo react" alt="React logo" />
              </a>
            </div>
            <h1>Vite + React</h1>
            <div className="card">
              <button onClick={() => setCount((count) => count + 1)}>
                count is {count}
              </button>
              <p>
                Edit <code>src/App.jsx</code> and save to test HMR
              </p>
            </div>
            <p className="read-the-docs">
              Click on the Vite and React logos to learn more
            </p>
          </header>
          <h1 className="text-center mt-5">React WebSocket App</h1>
          <div className="row mt-4">
            <div className="col-12">
              <div className="list-group">
                {messages.map((msg, index) => (
                  <div className="list-group-item" key={index}>
                    {msg}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="row mt-3">
            <div className="col-12">
              <div className="input-group">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Type a message"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                />
                <div className="input-group-append">
                  <button
                    className="btn btn-primary"
                    onClick={handleSendMessage}
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div> */}
      <div className="container-fluid" style={{height:'70px'}}>
      </div>
      <Bottom navlinks={navlinks} isMobile={isMobile}/>
    </ThemeProvider>
    
  );
}

export default App;

