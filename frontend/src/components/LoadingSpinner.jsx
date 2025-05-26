import React from "react";

const LoadingSpinner = ({ message = "Loading..." }) => {
  return (
    <div className="loading-container">
      <div className="loader"></div>
      <p>{message}</p>
    </div>
  );
};

export default LoadingSpinner;
