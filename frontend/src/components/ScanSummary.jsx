import React from "react";
import styles from "../styles/ScanSummary.module.css";

const ScanSummary = ({ scanSummary, onGenerateReport }) => {
  if (!scanSummary) return null;

  return (
    <div className={styles.scanSummary}>
      <div className={styles.cardHeader}>
        <h2>Scan Results Summary</h2>
      </div>
      <div className={styles.cardBody}>
        <div className={styles.summaryGrid}>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Targets Scanned</span>
            <span className={styles.summaryValue}>{scanSummary.targets}</span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Paths Checked</span>
            <span className={styles.summaryValue}>
              {scanSummary.totalPaths}
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Directories Found</span>
            <span className={styles.summaryValue}>
              {scanSummary.successfulPaths}
            </span>
          </div>
          <div className={styles.summaryItem}>
            <span className={styles.summaryLabel}>Duration</span>
            <span className={styles.summaryValue}>{scanSummary.duration}s</span>
          </div>
        </div>

        <button onClick={onGenerateReport} className={styles.btnPrimary}>
          <span className={styles.icon}>📊</span> Download Detailed Report
        </button>
      </div>
    </div>
  );
};

export default ScanSummary;
