import React from 'react';
import PropTypes from 'prop-types';

const Badge = ({ children, badgeContent, background = 'danger', isDot = false, size = 'small'  }) => {
  if (isDot) {
    return (
      <span
        className={`badge bg-${background} rounded-circle d-inline-block ${size === 'small' ? 'dot-small' : 'dot-large'}`}
        style={{
          width: '8px',
          height: '8px',
          minWidth: '8px',
          padding: '0',
          borderRadius: '50%',
          position: 'relative', // Ensure positioning works if needed
          top:'-10px',
        }}
      >
      </span>
    );
  }
  // Function to handle integer and word content formatting
  const formatBadgeContent = (content) => {
    // If the content is an integer, limit to 100+ if it's greater than 100
    if (typeof content === 'number') {
      return content > 100 ? '99+' : content;
    }
    // If the content is a string, truncate it if it's longer than 4 characters
    if (typeof content === 'string' && content.length > 4) {
      return `${content.substring(0, 4)}...`; // Truncate and append "..."
    }
    return content;
  };

  return (
    <span className={`badge badge-rounded bg-${background} ms-2`}>
      {children ? formatBadgeContent(children) : formatBadgeContent(badgeContent)}
    </span>
  );
};

// Prop Types for validation
Badge.propTypes = {
  badgeContent: PropTypes.node.isRequired, // badge content should be any renderable node (string, number, JSX)
  background: PropTypes.oneOf(['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']), // limited to Bootstrap badge background colors
  isDot: PropTypes.bool, // Determines if it's a dot badge or regular badge
  size: PropTypes.oneOf(['small', 'large']), // Optional: Define size of dot (small or large)
};

export default Badge;
