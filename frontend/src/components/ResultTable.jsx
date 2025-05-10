import React from "react";

const ResultTable = ({ results }) => {
  if (!results || Object.keys(results).length === 0) {
    return <p>결과가 없습니다.</p>;
  }

  // 성공한 결과만 필터링 (info가 존재하고, status_code가 200 또는 403인 경우)
  const successfulEntries = Object.entries(results).filter(
    ([url, info]) =>
      info && (info.status_code === 200 || info.status_code === 403)
  );

  if (successfulEntries.length === 0) {
    return <p>성공적인 스캔 결과가 없습니다. (발견된 디렉토리 없음)</p>;
  }

  return (
    <table
      border="1"
      cellPadding="8"
      style={{ width: "100%", marginTop: "20px", borderCollapse: "collapse" }}
    >
      <thead>
        <tr>
          <th style={{ border: "1px solid black", padding: "8px" }}>URL</th>
          <th style={{ border: "1px solid black", padding: "8px" }}>
            Status Code
          </th>
          <th style={{ border: "1px solid black", padding: "8px" }}>
            Content Length
          </th>
          <th style={{ border: "1px solid black", padding: "8px" }}>
            Directory Listing 여부
          </th>
        </tr>
      </thead>
      <tbody>
        {successfulEntries.map(([url, info]) => (
          <tr key={url}>
            <td style={{ border: "1px solid black", padding: "8px" }}>{url}</td>
            {/* 필터링을 통해 info 객체는 항상 존재함 */}
            <td style={{ border: "1px solid black", padding: "8px" }}>
              {info.status_code}
            </td>
            <td style={{ border: "1px solid black", padding: "8px" }}>
              {info.content_length}
            </td>
            <td style={{ border: "1px solid black", padding: "8px" }}>
              {info.directory_listing ? "Yes" : "No"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default ResultTable;
