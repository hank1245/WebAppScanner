import React from "react";

const HelpModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="help-overlay">
      <div className="help-content">
        <h3>Scan Help</h3>
        <button className="help-close" onClick={onClose}>
          ×
        </button>
        <div className="help-section">
          <h4>Target URLs</h4>
          <p>
            Enter target URLs to scan, one per line. (e.g., http://example.com)
          </p>
        </div>
        <div className="help-section">
          <h4>Mode</h4>
          <p>
            <strong>Normal:</strong> Standard website scanning
          </p>
          <p>
            <strong>Darkweb:</strong> Use Tor proxy for scanning .onion domains
          </p>
        </div>
        <div className="help-section">
          <h4>Maximum Depth</h4>
          <p>
            Set the maximum depth for recursive exploration of internal links.
            Higher values will increase scan time.
          </p>
        </div>
        <div className="help-section">
          <h4>Respect robots.txt Rules</h4>
          <p>
            Choose whether to follow access restriction rules specified in the
            website's robots.txt file.
          </p>
        </div>
        <div className="help-section">
          <h4>Exclusion List</h4>
          <p>Enter domains or URLs to exclude from scanning, one per line.</p>
        </div>
        <div className="help-section">
          <h4>Dictionary Settings</h4>
          <p>
            Edit the list of directories to scan. You can use the default
            dictionary or add/remove custom items.
          </p>
        </div>
      </div>
    </div>
  );
};

export default HelpModal;
