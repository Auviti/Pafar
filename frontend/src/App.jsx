import React, { useState, useEffect, useMemo  } from 'react';
import reactLogo from './assets/react.svg'
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
    { name: 'DashBoard', icon:<Icon icon='mdi:home' width={24} height={24} />, active: true, onClick: () => alert('Home clicked'),badgeContent: 'New'},
    { name: 'Inbox', icon:<Icon icon='mdi:inbox' width={24} height={24} />, active: false, onClick: () => alert('About clicked'),badgeContent: 500  },
    { name: 'Calender', icon:<Icon icon='mdi:calendar' width={24} height={24} />, active: false, onClick: () => alert('Calender clicked') },
    { name: 'About', icon:<Icon icon='mdi:information' width={24} height={24} />, active: false, onClick: () => alert('About clicked') },
    { name: 'Contact Us', icon:<Icon icon='mdi:phone' width={24} height={24} />, active: false, onClick: () => alert('Contact clicked') },
  ];

  return (
    <ThemeProvider>
      <Top navlinks={navlinks} isMobile={isMobile}/>
      <div className="container-fluid" style={{height:'70px'}}>
        </div>
      <div className="container-fluid">
        <div className={`row ${!isMobile?'mx-5':''}`}>
          <div className="col-12">
            <div class="row">
              <div className="col-12 col-sm-8">
                
              </div>
              <div className="col-12 col-sm-4">
                <span className='d-flex justify-content-end gap-2'>
                  <Button >clichghff</Button>
                  <Button >clichghff</Button>
                </span>
              </div>
            </div>
          </div>
          <div class="col-12 py-2">
            <div class="row">
              <div class="col-12 col-sm-6 col-md-4 col-lg-3 col-xl-3 p-1">
              <div class="card" style={{width: "18rem;"}}>
  <div class="card-body">
    <h5 class="card-title">Card title</h5>
    <h6 class="card-subtitle mb-2 text-body-secondary">Card subtitle</h6>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
    <a href="#" class="card-link">Card link</a>
    <a href="#" class="card-link">Another link</a>
  </div>
</div>
              </div>
              <div class="col-12 col-sm-6 col-md-4 col-lg-3 col-xl-3 p-1">
              <div class="card" style={{width: "18rem;"}}>
  <div class="card-body">
    <h5 class="card-title">Card title</h5>
    <h6 class="card-subtitle mb-2 text-body-secondary">Card subtitle</h6>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
    <a href="#" class="card-link">Card link</a>
    <a href="#" class="card-link">Another link</a>
  </div>
</div>
              </div>
              <div class="col-12 col-sm-6 col-md-4 col-lg-3 col-xl-3 p-1">
              <div class="card" style={{width: "18rem;"}}>
  <div class="card-body">
    <h5 class="card-title">Card title</h5>
    <h6 class="card-subtitle mb-2 text-body-secondary">Card subtitle</h6>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
    <a href="#" class="card-link">Card link</a>
    <a href="#" class="card-link">Another link</a>
  </div>
</div>
              </div>
              <div class="col-12 col-sm-6 col-md-4 col-lg-3 col-xl-3 p-1">
              <div class="card" style={{width: "18rem;"}}>
  <div class="card-body">
    <h5 class="card-title">Card title</h5>
    <h6 class="card-subtitle mb-2 text-body-secondary">Card subtitle</h6>
    <p class="card-text">Some quick example text to build on the card title and make up the bulk of the card's content.</p>
    <a href="#" class="card-link">Card link</a>
    <a href="#" class="card-link">Another link</a>
  </div>
</div>
              </div>
            </div>

          </div>
          <div class="col-12">
            Column
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

