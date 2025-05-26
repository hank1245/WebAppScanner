import React from "react";
import styles from "../styles/Footer.module.css";

const Footer = () => {
  return (
    <footer className={styles.appFooter}>
      <p>
        © Directory Tracer by Hank Kim | Please ensure you have legal
        authorization before scanning target websites. The developer is not
        responsible for any legal issues that may arise.
      </p>
    </footer>
  );
};

export default Footer;
