import React from "react";
import styles from "../styles/ScanSummary.module.css";

const ScanSummary = ({ summary, onGenerateReport }) => {
  if (!summary) return null;

  return (
    <div className={styles.scanSummary}>
      <div className={styles.cardHeader}>
        <h2>Scan Results Summary</h2>
      </div>
      <div className={styles.cardBody}>
        <div className={styles.summaryGrid}>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Targets Scanned</span>
            <span className={styles.summaryValue}>{summary.targets}</span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Total Paths Checked</span>
            <span className={styles.summaryValue}>{summary.totalPaths}</span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Directories Found</span>
            <span className={styles.summaryValue}>
              {summary.successfulPaths}
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>API Endpoints Found</span>
            <span className={styles.summaryValue}>
              {summary.foundApiEndpoints !== undefined
                ? summary.foundApiEndpoints
                : "N/A"}
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Scan Duration</span>
            <span className={styles.summaryValue}>{summary.duration}s</span>
          </div>
        </div>
        {onGenerateReport && (
          <div className={styles.reportButtonContainer}>
            <button onClick={onGenerateReport} className={styles.btnPrimary}>
              <span className={styles.icon}>📄</span> Generate Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanSummary;
