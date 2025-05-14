import React, { useState } from "react";

const ResultTable = ({ results }) => {
  const [sortField, setSortField] = useState("url");
  const [sortDirection, setSortDirection] = useState("asc");

  if (!results || Object.keys(results).length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📂</div>
        <p>아직 스캔 결과가 없습니다.</p>
        <p className="empty-hint">
          위 폼에서 타겟 URL을 입력하고 스캔을 시작하세요.
        </p>
      </div>
    );
  }

  // 성공한 결과만 필터링 (info가 존재하고, status_code가 200 또는 403인 경우)
  const successfulEntries = Object.entries(results).filter(
    ([_, info]) =>
      info && (info.status_code === 200 || info.status_code === 403)
  );

  if (successfulEntries.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔍</div>
        <p>발견된 디렉토리가 없습니다.</p>
        <p className="empty-hint">
          스캔은 완료되었지만 접근 가능한 디렉토리를 찾지 못했습니다.
        </p>
      </div>
    );
  }

  // 정렬 함수
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

  // 상태 코드에 따른 색상 반환
  const getStatusStyle = (code) => {
    if (code === 200) return { color: "#28a745" }; // 성공 - 녹색
    if (code === 403) return { color: "#fd7e14" }; // 접근 금지 - 주황색
    return {};
  };

  return (
    <div className="table-responsive">
      <table className="result-table">
        <thead>
          <tr>
            <th
              className={sortField === "url" ? `sorted ${sortDirection}` : ""}
              onClick={() => handleSort("url")}
            >
              URL
              <span className="sort-icon"></span>
            </th>
            <th
              className={
                sortField === "status" ? `sorted ${sortDirection}` : ""
              }
              onClick={() => handleSort("status")}
            >
              상태 코드
              <span className="sort-icon"></span>
            </th>
            <th
              className={
                sortField === "length" ? `sorted ${sortDirection}` : ""
              }
              onClick={() => handleSort("length")}
            >
              콘텐츠 길이
              <span className="sort-icon"></span>
            </th>
            <th
              className={
                sortField === "listing" ? `sorted ${sortDirection}` : ""
              }
              onClick={() => handleSort("listing")}
            >
              디렉토리 리스팅
              <span className="sort-icon"></span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedEntries.map(([url, info]) => (
            <tr key={url}>
              <td className="url-cell">
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
                  <span className="badge success">활성화됨</span>
                ) : (
                  <span className="badge neutral">비활성화</span>
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
