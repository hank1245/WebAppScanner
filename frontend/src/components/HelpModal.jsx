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
          <h4>Session Cookies (Optional)</h4>
          <p>
            If the target website requires authentication to access certain
            areas, you can provide your browser's session cookie string. The
            scanner will use these cookies for its requests.
          </p>
          <p>
            <strong>How to get cookies:</strong>
            <ol>
              <li>Log in to the target website in your browser.</li>
              <li>Open your browser's Developer Tools (usually F12).</li>
              <li>
                Go to the "Application" (Chrome/Edge) or "Storage" (Firefox)
                tab.
              </li>
              <li>Find "Cookies" under the Storage section for the website.</li>
              <li>
                Copy the relevant session cookie(s) as a string. For example,
                <code>cookieName1=cookieValue1; cookieName2=cookieValue2</code>.
                Ensure you copy only the necessary session cookies.
              </li>
            </ol>
          </p>
          <p>
            <strong>Note:</strong> Providing session cookies allows the scanner
            to operate as if you are logged in. Be cautious with sensitive
            session information. Cookies are sent to the backend to be used in
            requests but are not stored long-term or in reports (only a flag
            indicating if they were provided is stored).
          </p>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
