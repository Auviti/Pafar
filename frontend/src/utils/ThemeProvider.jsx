// ThemeProvider.js
import React, { useState, useEffect } from 'react';
import { themes } from './Themes'; // Import the theme constants

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState('light'); // Default theme is 'light'

  // Set the theme dynamically by changing the CSS variables
  const setAppTheme = (themeName) => {
    const themeStyles = themes[themeName];
    for (let key in themeStyles) {
      document.documentElement.style.setProperty(key, themeStyles[key]);
    }
  };

  // Update the theme whenever the theme state changes
  useEffect(() => {
    setAppTheme(theme);
  }, [theme]);

  return (
    <div>
      {/* <button
        onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
        className="btn btn-secondary"
      >
        Switch to {theme === 'light' ? 'Dark' : 'Light'} Theme
      </button> */}
      {children}
    </div>
  );
};

export default ThemeProvider;
