import React, { useState } from "react";

const ScanForm = ({ onScan }) => {
  const [targetUrl, setTargetUrl] = useState("");
  const [mode, setMode] = useState("normal");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!targetUrl) {
      alert("타겟 URL을 입력하세요.");
      return;
    }
    onScan(targetUrl, mode);
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
      <input
        type="text"
        placeholder="타겟 URL 입력 (ex: http://testphp.vulnweb.com)"
        value={targetUrl}
        onChange={(e) => setTargetUrl(e.target.value)}
        style={{ width: "400px", padding: "8px" }}
      />
      <select
        value={mode}
        onChange={(e) => setMode(e.target.value)}
        style={{ marginLeft: "10px", padding: "8px" }}
      >
        <option value="normal">Normal</option>
        <option value="darkweb">Darkweb (.onion)</option>
      </select>
      <button type="submit" style={{ marginLeft: "10px", padding: "8px 12px" }}>
        스캔 시작
      </button>
    </form>
  );
};

export default ScanForm;
