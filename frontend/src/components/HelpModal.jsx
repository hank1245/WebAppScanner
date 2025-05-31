import React from "react";
import styles from "../styles/HelpModal.module.css";

const HelpModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className={styles.helpOverlay}>
      <div className={styles.helpContent}>
        <h3>Scan Help</h3>
        <button className={styles.helpClose} onClick={onClose}>
          ×
        </button>
        <div className={styles.helpSection}>
          <h4>Target URLs</h4>
          <p>
            Enter target URLs to scan, one per line. (e.g., http://example.com)
          </p>
        </div>
        <div className={styles.helpSection}>
          <h4>Mode</h4>
          <p>
            <strong>Normal:</strong> Standard website scanning
          </p>
          <p>
            <strong>Darkweb:</strong> Use Tor proxy for scanning .onion domains
          </p>
        </div>
        <div className={styles.helpSection}>
          <h4>Maximum Depth</h4>
          <p>
            Set the maximum depth for recursive exploration of internal links.
            Higher values will increase scan time.
          </p>
        </div>
        <div className={styles.helpSection}>
          <h4>Respect robots.txt Rules</h4>
          <p>
            Choose whether to follow access restriction rules specified in the
            website's robots.txt file.
          </p>
        </div>
        <div className={styles.helpSection}>
          <h4>Exclusion List</h4>
          <p>Enter domains or URLs to exclude from scanning, one per line.</p>
        </div>
        <div className={styles.helpSection}>
          <h4>Dictionary Settings</h4>
          <p>
            Edit the list of directories to scan. You can use the default
            dictionary or add/remove custom items.
          </p>
        </div>
        <div className={styles.helpSection}>
          <h4>Login Credentials (Optional)</h4>
          <p>
            If the target website requires authentication to access certain
            areas, you can provide a username and password. The scanner will
            attempt to log in before scanning.
          </p>
          <p>
            <strong>Note:</strong> This feature attempts to log in using common
            login paths (e.g., /login, /signin) and form field names. It may not
            work for all websites. It is primarily intended for testing your own
            site where you control or understand the login mechanism. Passwords
            are sent to the backend for the login attempt but are not stored
            long-term or in reports.
          </p>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
