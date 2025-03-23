import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect, useMemo  } from 'react';
import { WebSocketService } from './utils/webSockets';  // Import the WebSocketService
import ThemeProvider from './utils/ThemeProvider'; // Import the ThemeProvider component


function App() {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');

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

  return (
    <ThemeProvider>
        <div className="container">
          <header className="App-header">
            <img src={logo} className="App-logo" alt="logo"/>
            <p>
              Edit <code>src/App.js</code> and save to reload.
            </p>
            <a
              className="App-link"
              href="https://reactjs.org"
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn React
            </a>
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
        </div>
    </ThemeProvider>
    
  );
}

export default App;
