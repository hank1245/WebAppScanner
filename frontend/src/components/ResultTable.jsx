import React, { useState, useMemo } from "react";
import styles from "../styles/ResultTable.module.css";

const ResultTable = ({ results }) => {
  const [statusFilter, setStatusFilter] = useState("ALL_SUCCESSFUL_AND_API");
  const [sortField, setSortField] = useState("url");
  const [sortDirection, setSortDirection] = useState("asc");

  const processedEntries = useMemo(() => {
    return Object.entries(results);
  }, [results]);

  const filteredAndSortedEntries = useMemo(() => {
    let filtered = processedEntries;

    if (statusFilter !== "ALL") {
      filtered = processedEntries.filter(([_, info]) => {
        if (!info) return false;
        const statusCodeStr = String(info.status_code);
        const source = info.source || "unknown";

        switch (statusFilter) {
          case "ALL_SUCCESSFUL_AND_API":
            return (
              (statusCodeStr === "200" || statusCodeStr === "403") &&
              ((source !== "js_api" && source !== "js_api_base") ||
                ((source === "js_api" || source === "js_api_base") &&
                  (statusCodeStr === "200" || statusCodeStr === "403")))
            );
          case "FOUND_API_ENDPOINTS":
            return (
              (source === "js_api" || source === "js_api_base") &&
              (statusCodeStr === "200" || statusCodeStr === "403")
            );
          case "ALL_SUCCESSFUL_NO_API":
            return (
              source !== "js_api" &&
              source !== "js_api_base" &&
              (statusCodeStr === "200" || statusCodeStr === "403")
            );
          case "EXCLUDED":
            return statusCodeStr === "EXCLUDED";
          case "NO_RESPONSE_OR_ERROR":
            return (
              statusCodeStr === "NO_RESPONSE_OR_ERROR" ||
              statusCodeStr === "SCANNER_TASK_ERROR"
            );
          default:
            return true;
        }
      });
    }

    const safeGet = (obj, path, defaultValue) => {
      return obj && obj[path] !== undefined ? obj[path] : defaultValue;
    };

    if (sortField !== null) {
      filtered.sort(([urlA, infoA], [urlB, infoB]) => {
        let comparison = 0;

        switch (sortField) {
          case "url":
            comparison = urlA.localeCompare(urlB);
            break;
          case "status":
            comparison = String(
              safeGet(infoA, "status_code", "")
            ).localeCompare(String(safeGet(infoB, "status_code", "")));
            break;
          case "size":
            comparison =
              safeGet(infoA, "content_length", 0) -
              safeGet(infoB, "content_length", 0);
            break;
          case "listing":
            const listingA = safeGet(infoA, "directory_listing", false);
            const listingB = safeGet(infoB, "directory_listing", false);
            if (safeGet(infoA, "source", "unknown") === "js_api")
              comparison = -1;
            else if (safeGet(infoB, "source", "unknown") === "js_api")
              comparison = 1;
            else if (listingA === listingB) comparison = 0;
            else if (listingA) comparison = 1;
            else comparison = -1;
            break;
          case "source":
            comparison = String(
              safeGet(infoA, "source", "unknown")
            ).localeCompare(String(safeGet(infoB, "source", "unknown")));
            break;
          default:
            comparison = 0;
        }

        return sortDirection === "asc" ? comparison : -comparison;
      });
    }

    return filtered;
  }, [processedEntries, statusFilter, sortField, sortDirection]);

  const handleSort = (field) => {
    if (field === sortField) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const getStatusStyle = (code) => {
    const codeStr = String(code);
    if (codeStr === "200") return { color: "#28a745" };
    if (codeStr === "403") return { color: "#ffc107" };
    if (codeStr === "404") return { color: "#dc3545" };
    if (codeStr && codeStr.startsWith("4")) return { color: "#dc3545" };
    if (codeStr && codeStr.startsWith("5"))
      return { color: "#dc3545", fontWeight: "bold" };
    return {};
  };

  if (processedEntries.length === 0) {
    return (
      <div className={styles.emptyState}>
        <div className={styles.emptyIcon}>📂</div>
        <p>No scan results yet.</p>
        <p className={styles.emptyHint}>
          Enter target URLs, select options, and start scanning.
        </p>
      </div>
    );
  }

  const filterOptions = [
    { value: "ALL_SUCCESSFUL_AND_API", label: "Found (Dirs & APIs: 200, 403)" },
    { value: "FOUND_API_ENDPOINTS", label: "Found API Endpoints (200, 403)" },
    {
      value: "ALL_SUCCESSFUL_NO_API",
      label: "Found Directories (200, 403, No APIs)",
    },
    { value: "ALL", label: "All Attempted Paths" },
    { value: "EXCLUDED", label: "Excluded Paths" },
    { value: "NO_RESPONSE_OR_ERROR", label: "Errors/No Response" },
  ];

  const getSourceDisplayName = (source) => {
    switch (source) {
      case "initial":
        return "Initial Scan";
      case "crawl":
        return "Crawled Page Scan";
      case "js_api":
        return "JS API Path";
      case "js_api_base":
        return "JS API Base";
      case "target_base":
        return "Target Base URL";
      default:
        return source || "Unknown";
    }
  };

  return (
    <div className={styles.resultTableContainer}>
      <div className={styles.tableControls}>
        <div className={styles.filterControl}>
          <label>
            Filter:
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className={styles.select}
            >
              {filterOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className={styles.resultCount}>
          {filteredAndSortedEntries.length} results
        </div>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.resultTable}>
          <thead>
            <tr>
              <th
                className={`${styles.urlColumn} ${
                  sortField === "url" ? styles.sorted : ""
                } ${sortField === "url" && styles[sortDirection]}`}
                onClick={() => handleSort("url")}
              >
                URL
                {sortField === "url" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th
                className={`${styles.statusColumn} ${
                  sortField === "status" ? styles.sorted : ""
                } ${sortField === "status" && styles[sortDirection]}`}
                onClick={() => handleSort("status")}
              >
                Status
                {sortField === "status" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th
                className={`${styles.sizeColumn} ${
                  sortField === "size" ? styles.sorted : ""
                } ${sortField === "size" && styles[sortDirection]}`}
                onClick={() => handleSort("size")}
              >
                Size
                {sortField === "size" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th
                className={`${styles.listingColumn} ${
                  sortField === "listing" ? styles.sorted : ""
                } ${sortField === "listing" && styles[sortDirection]}`}
                onClick={() => handleSort("listing")}
              >
                Directory Listing
                {sortField === "listing" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th
                className={`${styles.sourceColumn} ${
                  sortField === "source" ? styles.sorted : ""
                } ${sortField === "source" && styles[sortDirection]}`}
                onClick={() => handleSort("source")}
              >
                Source
                {sortField === "source" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th className={styles.noteColumn}>Note</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedEntries.map(([url, info]) => (
              <tr key={url} className={styles.resultRow}>
                <td className={styles.urlColumn}>
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.urlLink}
                  >
                    {url}
                  </a>
                </td>
                <td
                  className={styles.statusColumn}
                  style={getStatusStyle(info?.status_code)}
                >
                  {info?.status_code || "N/A"}
                </td>
                <td className={styles.sizeColumn}>
                  {info?.content_length !== undefined
                    ? `${info.content_length.toLocaleString()} bytes`
                    : "N/A"}
                </td>
                <td className={styles.listingColumn}>
                  {info?.directory_listing ? (
                    <span className={styles.directoryListingEnabled}>
                      Enabled
                    </span>
                  ) : (
                    "No"
                  )}
                </td>
                <td className={styles.sourceColumn}>
                  {getSourceDisplayName(info?.source)}
                </td>
                <td className={styles.noteColumn}>{info?.note || "N/A"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ResultTable;
