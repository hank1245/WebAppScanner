import React, { useState } from "react";
import DictionaryEditor from "./DictionaryEditor";
import HelpModal from "./HelpModal";

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
      dictionaryConfig.useDefault
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

      <form onSubmit={handleSubmit} className="scan-form">
        <div className="form-header">
          <button type="button" className="help-button" onClick={toggleHelp}>
            Help
          </button>
        </div>

        <div className="form-group">
          <label htmlFor="targetUrls">
            <span className="form-label">Target URL List</span>
            <span className="form-hint">Enter one per line</span>
          </label>
          <textarea
            id="targetUrls"
            placeholder="e.g., http://example.com"
            value={targetUrlsInput}
            onChange={(e) => setTargetUrlsInput(e.target.value)}
            rows="3"
            className="form-control"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="scanMode">
              <span className="form-label">Scan Mode</span>
            </label>
            <select
              id="scanMode"
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="form-control"
            >
              <option value="normal">Normal</option>
              <option value="darkweb">Darkweb (.onion)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="maxDepth">
              <span className="form-label">Maximum Crawling Depth</span>
            </label>
            <input
              id="maxDepth"
              type="number"
              value={maxDepth}
              onChange={(e) => setMaxDepth(e.target.value)}
              min="0"
              max="5"
              className="form-control"
            />
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={respectRobotsTxt}
                onChange={(e) => setRespectRobotsTxt(e.target.checked)}
                className="form-checkbox"
              />
              <span>Respect robots.txt rules</span>
            </label>
          </div>
        </div>

        <div className="form-group dictionary-section">
          <DictionaryEditor onChange={handleDictionaryChange} />
        </div>

        <div className="form-group">
          <label htmlFor="exclusions">
            <span className="form-label">Domains or URLs to Exclude</span>
            <span className="form-hint">Enter one per line</span>
          </label>
          <textarea
            id="exclusions"
            placeholder="e.g., admin.example.com"
            value={exclusions}
            onChange={(e) => setExclusions(e.target.value)}
            rows="2"
            className="form-control"
          />
        </div>

        <button type="submit" className="btn btn-primary scan-button">
          <span className="icon">🔍</span> Start Scan
        </button>
      </form>
    </>
  );
};

export default ScanForm;
