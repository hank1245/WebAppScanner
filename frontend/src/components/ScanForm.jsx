import React, { useState } from "react";

const ScanForm = ({ onScan }) => {
  const [targetUrlsInput, setTargetUrlsInput] = useState(""); // Changed from targetUrl to targetUrlsInput
  const [mode, setMode] = useState("normal");
  const [exclusions, setExclusions] = useState("");
  const [maxDepth, setMaxDepth] = useState(2);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!targetUrlsInput.trim()) {
      alert("타겟 URL 또는 IP 목록을 입력하세요.");
      return;
    }
    const targetList = targetUrlsInput
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item);

    if (targetList.length === 0) {
      alert("유효한 타겟 URL 또는 IP를 입력하세요.");
      return;
    }

    const exclusionList = exclusions
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => item);
    onScan(targetList, mode, exclusionList, parseInt(maxDepth, 10)); // Pass targetList
  };

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: "20px" }}>
      <div style={{ marginBottom: "10px" }}>
        <textarea
          placeholder="타겟 URL 또는 IP 목록 (한 줄에 하나씩 입력, ex: http://testphp.vulnweb.com)"
          value={targetUrlsInput}
          onChange={(e) => setTargetUrlsInput(e.target.value)}
          rows="3"
          style={{
            width: "calc(100% - 22px)",
            padding: "8px",
            boxSizing: "border-box",
          }}
        />
      </div>
      <div style={{ marginBottom: "10px" }}>
        <select
          value={mode}
          onChange={(e) => setMode(e.target.value)}
          style={{ padding: "8px", marginRight: "10px" }}
        >
          <option value="normal">Normal</option>
          <option value="darkweb">Darkweb (.onion)</option>
        </select>
        <input
          type="number"
          value={maxDepth}
          onChange={(e) => setMaxDepth(e.target.value)}
          min="0"
          style={{
            padding: "8px",
            width: "70px",
            marginRight: "10px",
          }}
          title="Max Depth"
        />
      </div>
      <div style={{ marginBottom: "10px" }}>
        <textarea
          placeholder="제외할 도메인 또는 IP 목록 (한 줄에 하나씩 입력)"
          value={exclusions}
          onChange={(e) => setExclusions(e.target.value)}
          rows="3"
          style={{
            width: "calc(100% - 22px)",
            padding: "8px",
            boxSizing: "border-box",
          }}
        />
      </div>
      <button type="submit" style={{ padding: "10px 15px" }}>
        스캔 시작
      </button>
    </form>
  );
};

export default ScanForm;
