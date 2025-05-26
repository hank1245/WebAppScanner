import React, { useState } from "react";
import styles from "../styles/ResultTable.module.css";

const ResultTable = ({ results }) => {
  const [sortField, setSortField] = useState("url");
  const [sortDirection, setSortDirection] = useState("asc");

  if (!results || Object.keys(results).length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📂</div>
        <p>No scan results yet.</p>
        <p className={styles.emptyHint}>
          Enter target URLs in the form above and start scanning.
        </p>
      </div>
    );
  }

  // Filter only successful results (info exists and status_code is 200 or 403)
  const successfulEntries = Object.entries(results).filter(
    ([_, info]) =>
      info && (info.status_code === 200 || info.status_code === 403)
  );

  if (successfulEntries.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>🔍</div>
        <p>No directories found.</p>
        <p className={styles.emptyHint}>
          Scan completed but no accessible directories were discovered.
        </p>
      </div>
    );
  }

  // Sorting function
  const sortResults = (a, b) => {
    const [urlA, infoA] = a;
    const [urlB, infoB] = b;

    let comparison = 0;

    switch (sortField) {
      case "url":
        comparison = urlA.localeCompare(urlB);
        break;
      case "status":
        comparison = infoA.status_code - infoB.status_code;
        break;
      case "length":
        comparison = infoA.content_length - infoB.content_length;
        break;
      case "listing":
        comparison =
          infoA.directory_listing === infoB.directory_listing
            ? 0
            : infoA.directory_listing
            ? 1
            : -1;
        break;
      default:
        comparison = 0;
    }

    return sortDirection === "asc" ? comparison : -comparison;
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const sortedEntries = [...successfulEntries].sort(sortResults);

  // Return color style based on status code
  const getStatusStyle = (code) => {
    if (code === 200) return { color: "#28a745" }; // Success - green
    if (code === 403) return { color: "#fd7e14" }; // Forbidden - orange
    return {};
  };

  return (
    <div className={styles.tableResponsive}>
      <table className={styles.resultTable}>
        <thead>
          <tr>
            <th
              className={
                sortField === "url"
                  ? `${styles.sorted} ${styles[sortDirection]}`
                  : ""
              }
              onClick={() => handleSort("url")}
            >
              URL
              <span className={styles.sortIcon}></span>
            </th>
            <th
              className={
                sortField === "status"
                  ? `${styles.sorted} ${styles[sortDirection]}`
                  : ""
              }
              onClick={() => handleSort("status")}
            >
              Status Code
              <span className={styles.sortIcon}></span>
            </th>
            <th
              className={
                sortField === "length"
                  ? `${styles.sorted} ${styles[sortDirection]}`
                  : ""
              }
              onClick={() => handleSort("length")}
            >
              Content Length
              <span className={styles.sortIcon}></span>
            </th>
            <th
              className={
                sortField === "listing"
                  ? `${styles.sorted} ${styles[sortDirection]}`
                  : ""
              }
              onClick={() => handleSort("listing")}
            >
              Directory Listing
              <span className={styles.sortIcon}></span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedEntries.map(([url, info]) => (
            <tr key={url}>
              <td className={styles.urlCell}>
                <a
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={url}
                >
                  {url}
                </a>
              </td>
              <td style={getStatusStyle(info.status_code)}>
                {info.status_code}
              </td>
              <td>{info.content_length.toLocaleString()}</td>
              <td>
                {info.directory_listing ? (
                  <span className={`${styles.badge} ${styles.success}`}>
                    Enabled
                  </span>
                ) : (
                  <span className={`${styles.badge} ${styles.neutral}`}>
                    Disabled
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultTable;
