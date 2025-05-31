import React, { useState, useMemo } from "react";
import styles from "../styles/ResultTable.module.css"; // CSS 모듈 경로 확인

const ResultTable = ({ results }) => {
  const [sortField, setSortField] = useState("url");
  const [sortDirection, setSortDirection] = useState("asc");
  const [statusFilter, setStatusFilter] = useState("ALL_SUCCESSFUL");

  const processedEntries = useMemo(() => {
    if (!results || Object.keys(results).length === 0) {
      return [];
    }
    return Object.entries(results);
  }, [results]);

  // 정렬 및 필터링 로직
  const filteredAndSortedEntries = useMemo(() => {
    let filtered = processedEntries;

    if (statusFilter !== "ALL") {
      filtered = processedEntries.filter(([_, info]) => {
        if (!info) return false;
        const statusCodeStr = String(info.status_code);
        switch (statusFilter) {
          case "ALL_SUCCESSFUL":
            return statusCodeStr === "200" || statusCodeStr === "403";
          case "200":
            return statusCodeStr === "200";
          case "403":
            return statusCodeStr === "403";
          case "EXCLUDED":
            return statusCodeStr === "EXCLUDED";
          case "NO_RESPONSE_OR_ERROR":
            return (
              statusCodeStr === "NO_RESPONSE_OR_ERROR" ||
              statusCodeStr === "SCANNER_TASK_ERROR"
            );
          case "JS_API_SUCCESSFUL":
            return (
              (statusCodeStr === "200" || statusCodeStr === "403") &&
              info.source === "js_api"
            );
          case "JS_API_ALL":
            return info.source === "js_api";
          default:
            return true;
        }
      });
    }

    return [...filtered].sort((a, b) => {
      const [urlA, infoA] = a;
      const [urlB, infoB] = b;
      let comparison = 0;

      const safeGet = (obj, path, defaultValue) => {
        if (!obj) return defaultValue;
        const value = path
          .split(".")
          .reduce(
            (o, p) =>
              o && o[p] !== undefined && o[p] !== null ? o[p] : undefined,
            obj
          );
        return value === undefined ? defaultValue : value;
      };

      switch (sortField) {
        case "url":
          comparison = urlA.localeCompare(urlB);
          break;
        case "status":
          comparison = String(safeGet(infoA, "status_code", "")).localeCompare(
            String(safeGet(infoB, "status_code", ""))
          );
          break;
        case "length":
          comparison =
            safeGet(infoA, "content_length", 0) -
            safeGet(infoB, "content_length", 0);
          break;
        case "listing":
          const listingA = safeGet(infoA, "directory_listing", false);
          const listingB = safeGet(infoB, "directory_listing", false);
          if (listingA === listingB) comparison = 0;
          else if (listingA) comparison = 1;
          else comparison = -1;
          break;
        default:
          comparison = 0;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });
  }, [processedEntries, statusFilter, sortField, sortDirection]);

  // 정렬 핸들러 함수
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // 상태 코드 스타일 반환 함수
  const getStatusStyle = (codeStr) => {
    if (codeStr === "200") return { color: "#28a745", fontWeight: "bold" }; // Green
    if (codeStr === "403") return { color: "#fd7e14", fontWeight: "bold" }; // Orange
    if (
      ["EXCLUDED", "NO_RESPONSE_OR_ERROR", "SCANNER_TASK_ERROR"].includes(
        codeStr
      )
    )
      return { color: "#6c757d" }; // Grey
    if (codeStr && codeStr.startsWith("4")) return { color: "#dc3545" }; // Red for other 4xx
    if (codeStr && codeStr.startsWith("5"))
      return { color: "#dc3545", fontWeight: "bold" }; // Red for 5xx
    return {}; // Default
  };

  // 초기 결과가 없을 때 표시
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

  // 필터 옵션 정의
  const filterOptions = [
    { value: "ALL_SUCCESSFUL", label: "Successful (200, 403)" },
    { value: "ALL", label: "All Attempted Paths" },
    { value: "200", label: "Status 200 Only" },
    { value: "403", label: "Status 403 Only" },
    { value: "EXCLUDED", label: "Excluded Paths" },
    { value: "NO_RESPONSE_OR_ERROR", label: "Errors / No Response" },
    { value: "JS_API_SUCCESSFUL", label: "JS API (Successful)" },
    { value: "JS_API_ALL", label: "JS API (All Paths)" },
  ];

  return (
    <>
      <div className={styles.filterControls}>
        <label htmlFor="statusFilter">Filter Results: </label>
        <select
          id="statusFilter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={styles.filterSelect}
        >
          {filterOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {filteredAndSortedEntries.length === 0 ? (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🔍</div>
          <p>No results match the current filter.</p>
          <p className={styles.emptyHint}>
            Try adjusting the filter or scan new targets.
          </p>
        </div>
      ) : (
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
                  URL{" "}
                  {sortField === "url" && (
                    <span className={styles.sortIcon}></span>
                  )}
                </th>
                <th
                  className={
                    sortField === "status"
                      ? `${styles.sorted} ${styles[sortDirection]}`
                      : ""
                  }
                  onClick={() => handleSort("status")}
                >
                  Status{" "}
                  {sortField === "status" && (
                    <span className={styles.sortIcon}></span>
                  )}
                </th>
                <th
                  className={
                    sortField === "length"
                      ? `${styles.sorted} ${styles[sortDirection]}`
                      : ""
                  }
                  onClick={() => handleSort("length")}
                >
                  Length{" "}
                  {sortField === "length" && (
                    <span className={styles.sortIcon}></span>
                  )}
                </th>
                <th
                  className={
                    sortField === "listing"
                      ? `${styles.sorted} ${styles[sortDirection]}`
                      : ""
                  }
                  onClick={() => handleSort("listing")}
                >
                  Listing{" "}
                  {sortField === "listing" && (
                    <span className={styles.sortIcon}></span>
                  )}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredAndSortedEntries.map(([url, info]) => (
                <tr key={url}>
                  <td className={styles.urlCell}>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={url}
                    >
                      {" "}
                      {url}{" "}
                    </a>
                    {info && info.source === "js_api" && (
                      <span className={`${styles.badge} ${styles.info}`}>
                        JS API
                      </span>
                    )}
                  </td>
                  <td
                    style={getStatusStyle(info ? String(info.status_code) : "")}
                  >
                    {info ? String(info.status_code) : "N/A"}
                  </td>
                  <td>
                    {info && info.content_length !== undefined
                      ? info.content_length.toLocaleString()
                      : "N/A"}
                  </td>
                  <td>
                    {info && info.directory_listing !== undefined ? (
                      info.directory_listing ? (
                        <span className={`${styles.badge} ${styles.success}`}>
                          Enabled
                        </span>
                      ) : (
                        <span className={`${styles.badge} ${styles.neutral}`}>
                          Disabled
                        </span>
                      )
                    ) : (
                      "N/A"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
};

export default ResultTable;
