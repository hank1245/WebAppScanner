import React from "react";
import styles from "../styles/Header.module.css";

const Header = () => {
  return (
    <header className={styles.appHeader}>
      <h1>📁 Directory Tracer</h1>
      <p className={styles.appDescription}>
        A tool for exploring website directories and discovering hidden paths.
      </p>
    </header>
  );
};

export default Header;
