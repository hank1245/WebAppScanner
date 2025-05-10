import React, { useState } from "react";
import { scanWebsite } from "./api";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";

function App() {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);

  const handleScan = async (targetUrlList, mode, exclusions, maxDepth) => {
    setLoading(true);
    setResults({});
    try {
      const scanResult = await scanWebsite(
        targetUrlList,
        mode,
        exclusions,
        maxDepth
      );
      setResults(scanResult);
    } catch (error) {
      console.error("스캔 중 오류 발생:", error);
      alert("스캔에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>📁 디렉토리 스캐너</h1>
      <ScanForm onScan={handleScan} />
      {loading ? <p>스캔 중입니다...⏳</p> : <ResultTable results={results} />}
    </div>
  );
}

export default App;
