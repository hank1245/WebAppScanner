import React from "react";

const ScanSummary = ({ scanSummary, onGenerateReport }) => {
  if (!scanSummary) return null;

  return (
    <div className="card scan-summary">
      <div className="card-header">
        <h2>Scan Results Summary</h2>
      </div>
      <div className="card-body">
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Targets Scanned</span>
            <span className="summary-value">{scanSummary.targets}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Paths Checked</span>
            <span className="summary-value">{scanSummary.totalPaths}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Directories Found</span>
            <span className="summary-value">{scanSummary.successfulPaths}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Duration</span>
            <span className="summary-value">{scanSummary.duration}s</span>
          </div>
        </div>

        <button onClick={onGenerateReport} className="btn btn-primary">
          <span className="icon">📊</span> Download Detailed Report
        </button>
      </div>
    </div>
  );
};

export default ScanSummary;
