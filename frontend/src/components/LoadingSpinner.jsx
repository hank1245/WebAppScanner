import React from "react";
import styles from "../styles/LoadingSpinner.module.css";

const LoadingSpinner = ({ message = "Loading..." }) => {
  return (
    <div className={styles.loadingContainer}>
      <div className={styles.loader}></div>
      <p>{message}</p>
    </div>
  );
};

export default LoadingSpinner;
