import PropTypes from "prop-types";
import './Spinner.css';
// Spinner Component
const Spinner = ({ outline, size }) => {
  const spinnerClass = `spinner-border ${outline ? "spinner-outline-border" : ""} ${
    size ? `spinner-border-${size}` : "spinner-border-sm"
  }`;

  return <div className={spinnerClass} role="status"></div>;
};

// PropTypes validation
Spinner.propTypes = {
  outline: PropTypes.bool,  // Boolean to check if the spinner is outlined
  size: PropTypes.oneOf(["sm", "lg"]),  // Size options: "sm" for small, "lg" for large
};

export default Spinner;
