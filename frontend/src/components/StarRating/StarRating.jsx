import React, { useState } from 'react';
import PropTypes from 'prop-types';

const StarRating = ({ rating, onRatingChange }) => {
  const [currentRating, setCurrentRating] = useState(rating);

  const handleMouseEnter = (index) => {
    setCurrentRating(index);
  };

  const handleMouseLeave = () => {
    setCurrentRating(rating);
  };

  const handleClick = (index) => {
    onRatingChange(index);
  };

  const renderStars = () => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      const star = i <= currentRating ? '⭐' : '☆'; // Filled star (⭐) or empty star (☆)
      stars.push(
        <span
          key={i}
          className="star"
          onClick={() => handleClick(i)}
          onMouseEnter={() => handleMouseEnter(i)}
          onMouseLeave={handleMouseLeave}
        >
          {star}
        </span>
      );
    }
    return stars;
  };

  return <span>{renderStars()}</span>;
};

// Prop Types for validation
StarRating.propTypes = {
  rating: PropTypes.number, // Current rating value (default is 0)
  onRatingChange: PropTypes.func.isRequired, // Callback to update rating
};

StarRating.defaultProps = {
  rating: 0, // Default rating is 0
};

export default StarRating;
