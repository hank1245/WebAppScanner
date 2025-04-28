import React from "react";

const ResultTable = ({ results }) => {
  if (!results || Object.keys(results).length === 0) {
    return <p>결과가 없습니다.</p>;
  }

  return (
    <table
      border="1"
      cellPadding="8"
      style={{ width: "100%", marginTop: "20px" }}
    >
      <thead>
        <tr>
          <th>URL</th>
          <th>Status Code</th>
          <th>Content Length</th>
          <th>Directory Listing 여부</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(results).map(([url, info]) => (
          <tr key={url}>
            <td>{url}</td>
            <td>{info ? info.status_code : "Error"}</td>
            <td>{info ? info.content_length : "-"}</td>
            <td>{info ? (info.directory_listing ? "Yes" : "No") : "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default ResultTable;
