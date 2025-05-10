import React, { useState, useEffect } from "react";
import { scanWebsite } from "./api";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";

// Helper function to download JSON
const downloadJSON = (data, filename) => {
  const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
    JSON.stringify(data, null, 2)
  )}`;
  const link = document.createElement("a");
  link.href = jsonString;
  link.download = filename;
  document.body.appendChild(link); // Required for Firefox
  link.click();
  document.body.removeChild(link);
};

function App() {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [scanMetadata, setScanMetadata] = useState(null); // To store scan settings and timestamps

  const handleScan = async (targetUrlList, mode, exclusions, maxDepth) => {
    setLoading(true);
    setResults({});
    const startTime = new Date();
    setScanMetadata({
      targets: targetUrlList,
      exclusions: exclusions,
      maxDepth: maxDepth,
      startTime: startTime,
      endTime: null,
    });

    try {
      const scanResult = await scanWebsite(
        targetUrlList,
        mode,
        exclusions,
        maxDepth
      );
      setResults(scanResult);
      setScanMetadata((prev) => ({ ...prev, endTime: new Date() }));
    } catch (error) {
      console.error("스캔 중 오류 발생:", error);
      alert("스캔에 실패했습니다.");
      setScanMetadata((prev) => ({ ...prev, endTime: new Date() })); // Also set endTime on error
    } finally {
      setLoading(false);
    }
  };

  const generateReport = () => {
    if (!results || !scanMetadata || !scanMetadata.endTime) {
      alert("리포트를 생성할 데이터가 없습니다.");
      return;
    }

    const successfulEntries = Object.entries(results).filter(
      ([_, info]) =>
        info && (info.status_code === 200 || info.status_code === 403)
    );

    const reportData = {
      scan_completed_timestamp: scanMetadata.endTime.toISOString(),
      scan_duration_seconds:
        (scanMetadata.endTime.getTime() - scanMetadata.startTime.getTime()) /
        1000,
      targets_scanned_count: scanMetadata.targets.length,
      targets_list: scanMetadata.targets,
      max_depth: scanMetadata.maxDepth,
      exclusions_list: scanMetadata.exclusions,
      checked_paths_count: Object.keys(results).length, // Total paths for which backend returned a result
      successful_directories_count: successfulEntries.length,
      successful_directories_list: successfulEntries.map(([url, info]) => ({
        url: url,
        status_code: info.status_code,
        content_length: info.content_length,
        directory_listing: info.directory_listing,
      })),
    };

    downloadJSON(
      reportData,
      `scan_report_${new Date().toISOString().split("T")[0]}.json`
    );
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>📁 디렉토리 스캐너</h1>
      <ScanForm onScan={handleScan} />
      {loading ? (
        <p>스캔 중입니다...⏳</p>
      ) : (
        <>
          {Object.keys(results).length > 0 &&
            scanMetadata &&
            scanMetadata.endTime && (
              <button
                onClick={generateReport}
                style={{
                  marginTop: "10px",
                  marginBottom: "10px",
                  padding: "8px 12px",
                }}
              >
                리포트 다운로드 (JSON)
              </button>
            )}
          <ResultTable results={results} />
        </>
      )}
    </div>
  );
}

export default App;
