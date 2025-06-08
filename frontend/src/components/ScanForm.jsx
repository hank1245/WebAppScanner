import React, { useState } from "react";
import DictionaryEditor from "./DictionaryEditor";
import HelpModal from "./HelpModal";
import styles from "../styles/ScanForm.module.css";

const ScanForm = ({ onScan }) => {
  const [targetUrlsInput, setTargetUrlsInput] = useState("");
  const [mode, setMode] = useState("normal");
  const [exclusions, setExclusions] = useState("");
  const [maxDepth, setMaxDepth] = useState(2);
  const [respectRobotsTxt, setRespectRobotsTxt] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const [dictionaryConfig, setDictionaryConfig] = useState({
    operations: [],
    useDefault: true,
  });
  const [sessionCookies, setSessionCookies] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!targetUrlsInput.trim()) {
      alert("Please enter target URLs or IP addresses.");
      return;
    }
    const targetList = targetUrlsInput
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item);

    if (targetList.length === 0) {
      alert("Please enter valid target URLs or IP addresses.");
      return;
    }

    const exclusionList = exclusions
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item);

    onScan(
      targetList,
      mode,
      exclusionList,
      parseInt(maxDepth, 10),
      respectRobotsTxt,
      dictionaryConfig.operations,
      dictionaryConfig.useDefault,
      sessionCookies
    );
  };

  const toggleHelp = () => {
    setShowHelp(!showHelp);
  };

  const handleDictionaryChange = (config) => {
    setDictionaryConfig(config);
  };

  return (
    <>
      <HelpModal isOpen={showHelp} onClose={toggleHelp} />

      <form onSubmit={handleSubmit} className={styles.scanForm}>
        <div className={styles.formHeader}>
          <button
            type="button"
            className={styles.helpButton}
            onClick={toggleHelp}
          >
            Help
          </button>
          <h2 className={styles.formTitle}>Directory Scanner</h2>
          <button type="submit" className={styles.submitButton}>
            Start Scan
          </button>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="targetUrls">
            <span className={styles.formLabel}>Target URLs/IP Addresses</span>
            <span className={styles.formHint}>Enter one per line</span>
          </label>
          <textarea
            id="targetUrls"
            placeholder="e.g., http://example.com&#10;https://test.example.org"
            value={targetUrlsInput}
            onChange={(e) => setTargetUrlsInput(e.target.value)}
            rows="3"
            className={styles.formControl}
            required
          />
        </div>

        <div className={styles.formOptionsGrid}>
          <div className={styles.formGroup}>
            <label htmlFor="mode" className={styles.formLabel}>
              Scan Mode
            </label>
            <select
              id="mode"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className={styles.formControl}
            >
              <option value="normal">Normal</option>
              <option value="darkweb">Dark Web (via TOR)</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="maxDepth" className={styles.formLabel}>
              Max Crawling Depth
            </label>
            <select
              id="maxDepth"
              value={maxDepth}
              onChange={(e) => setMaxDepth(e.target.value)}
              className={styles.formControl}
            >
              <option value="0">0 - No Crawling</option>
              <option value="1">1 - First Level Only</option>
              <option value="2">2 - Two Levels Deep</option>
              <option value="3">3 - Three Levels Deep</option>
              <option value="4">4 - Four Levels Deep</option>
            </select>
          </div>

          <div className={styles.formGroup}>
            <label htmlFor="sessionCookies" className={styles.formLabel}>
              Session Cookies (Optional)
            </label>
            <input
              type="text"
              id="sessionCookies"
              placeholder="e.g., cookie1=value1; cookie2=value2"
              value={sessionCookies}
              onChange={(e) => setSessionCookies(e.target.value)}
              className={styles.formControl}
            />
            <div className={styles.formHint}>
              Include session cookies for authenticated scanning
            </div>
          </div>

          <div className={styles.formGroup}>
            <div className={styles.checkboxGroup}>
              <label className={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={respectRobotsTxt}
                  onChange={(e) => setRespectRobotsTxt(e.target.checked)}
                  className={styles.formCheckbox}
                />
                <span>Respect robots.txt rules</span>
              </label>
            </div>
          </div>
        </div>

        <div className={styles.formGroup}>
          <div className={styles.dictionarySection}>
            <DictionaryEditor onChange={handleDictionaryChange} />
          </div>
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="exclusions">
            <span className={styles.formLabel}>Domains or URLs to Exclude</span>
            <span className={styles.formHint}>Enter one per line</span>
          </label>
          <textarea
            id="exclusions"
            placeholder="e.g., admin.example.com"
            value={exclusions}
            onChange={(e) => setExclusions(e.target.value)}
            rows="2"
            className={styles.formControl}
          />
        </div>
      </form>
    </>
  );
};

export default ScanForm;
