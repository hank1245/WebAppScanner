import React, { useState, useMemo } from "react";
import styles from "../styles/ResultTable.module.css"; // CSS 모듈 경로 확인

const ResultTable = ({ results }) => {
  const [sortField, setSortField] = useState("url");
  const [sortDirection, setSortDirection] = useState("asc");
  // 초기 필터를 "ALL_SUCCESSFUL"로 설정하여 일반적인 성공 경로와 발견된 API 엔드포인트를 함께 표시
  const [statusFilter, setStatusFilter] = useState("ALL_SUCCESSFUL_AND_API");

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
        const source = info.source || "unknown";

        switch (statusFilter) {
          case "ALL_SUCCESSFUL_AND_API": // 기본 필터: 일반 성공 + JS API 성공
            return (
              (statusCodeStr === "200" || statusCodeStr === "403") &&
              (source !== "js_api" ||
                (source === "js_api" &&
                  (statusCodeStr === "200" || statusCodeStr === "403")))
            );
          case "FOUND_API_ENDPOINTS": // JS API 소스이고 200 또는 403인 경우
            return (
              source === "js_api" &&
              (statusCodeStr === "200" || statusCodeStr === "403")
            );
          case "ALL_SUCCESSFUL_NO_API": // API 제외한 성공
            return (
              source !== "js_api" &&
              (statusCodeStr === "200" || statusCodeStr === "403")
            );
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
          // case "JS_API_SUCCESSFUL": // FOUND_API_ENDPOINTS로 대체
          //   return (
          //     (statusCodeStr === "200" || statusCodeStr === "403") &&
          //     info.source === "js_api"
          //   );
          case "JS_API_ALL_ATTEMPTED": // JS API 소스의 모든 시도 (404 포함)
            return source === "js_api";
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
          if (safeGet(infoA, "source", "unknown") === "js_api")
            comparison = -1; // API는 항상 아래로 (또는 별도 처리)
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
    if (codeStr === "404") return { color: "#dc3545" }; // Red for 404
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
    { value: "ALL_SUCCESSFUL_AND_API", label: "Found (Dirs & APIs: 200, 403)" },
    { value: "FOUND_API_ENDPOINTS", label: "Found API Endpoints (200, 403)" },
    {
      value: "ALL_SUCCESSFUL_NO_API",
      label: "Found Directories (200, 403, No APIs)",
    },
    { value: "ALL", label: "All Attempted Paths" },
    { value: "200", label: "Status 200 Only" },
    { value: "403", label: "Status 403 Only" },
    {
      value: "JS_API_ALL_ATTEMPTED",
      label: "All Attempted API Paths (incl. 404)",
    },
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
        return "JS Discovered API";
      default:
        return source || "Unknown";
    }
  };

  return (
    <div className={styles.resultTableContainer}>
      <div className={styles.filterControls}>
        <label htmlFor="statusFilter">Filter by:</label>
        <select
          id="statusFilter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={styles.filterSelect}
        >
          {filterOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {filteredAndSortedEntries.length === 0 && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🧐</div>
          <p>No results match the current filter.</p>
        </div>
      )}

      {filteredAndSortedEntries.length > 0 && (
        <table className={styles.resultTable}>
          <thead>
            <tr>
              <th onClick={() => handleSort("url")}>
                URL
                {sortField === "url" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort("status")}>
                Status
                {sortField === "status" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort("length")}>
                Length
                {sortField === "length" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort("listing")}>
                Dir. Listing
                {sortField === "listing" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th onClick={() => handleSort("source")}>
                Source
                {sortField === "source" && (
                  <span className={styles.sortIcon}>
                    {sortDirection === "asc" ? "▲" : "▼"}
                  </span>
                )}
              </th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedEntries.map(([url, info]) => (
              <tr key={url}>
                <td className={styles.urlCell}>
                  <a href={url} target="_blank" rel="noopener noreferrer">
                    {url}
                  </a>
                </td>
                <td style={getStatusStyle(String(info.status_code))}>
                  {String(info.status_code)}
                </td>
                <td>{info.content_length}</td>
                <td>
                  {info.source === "js_api" ? (
                    <span className={styles.badgeNeutral}>N/A (API)</span>
                  ) : info.directory_listing ? (
                    <span className={styles.badgeDanger}>Enabled</span>
                  ) : (
                    <span className={styles.badgeSuccess}>Disabled</span>
                  )}
                </td>
                <td>
                  <span
                    className={`${styles.badge} ${
                      styles[
                        `sourceBadge${getSourceDisplayName(info.source).replace(
                          /\s+/g,
                          ""
                        )}`
                      ] || styles.badgeNeutral
                    }`}
                  >
                    {getSourceDisplayName(info.source)}
                  </span>
                </td>
                <td>{info.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ResultTable;
