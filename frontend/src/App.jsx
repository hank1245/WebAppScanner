import React from "react";
import styles from "./App.module.css";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";
import LoadingSpinner from "./components/LoadingSpinner";
import ScanSummary from "./components/ScanSummary"; // ScanSummary 컴포넌트가 있다고 가정
import { useScan } from "./hooks/useScan";
import { useReportGenerator } from "./hooks/useReportGenerator";
import HelpModal from "./components/HelpModal"; // HelpModal 추가 (필요시)

function App() {
  const {
    results,
    loading,
    scanMetadata,
    rawScanData, // rawScanData도 가져옴
    handleScan,
    getScanSummary, // getScanSummary 함수를 직접 사용
    scanError, // scanError 가져옴
  } = useScan();
  const { generateReport } = useReportGenerator(
    results,
    scanMetadata,
    rawScanData
  );

  // HelpModal 상태 (예시)
  const [showHelp, setShowHelp] = React.useState(false);
  const toggleHelp = () => setShowHelp(!showHelp);

  const scanSummaryData = getScanSummary(); // 요약 데이터 가져오기

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>Directory Tracer</h1>
        <button onClick={toggleHelp} className={styles.helpButton}>
          ?
        </button>
      </header>
      {showHelp && <HelpModal onClose={toggleHelp} />}

      <main className={styles.mainContent}>
        <ScanForm onScan={handleScan} isLoading={loading} />
        {loading && <LoadingSpinner />}
        {scanError && (
          <div className={styles.errorMessage}>{scanError}</div>
        )}{" "}
        {/* 에러 메시지 표시 */}
        {!loading &&
          !scanError &&
          scanSummaryData && ( // scanSummaryData 사용
            <ScanSummary
              summary={scanSummaryData}
              onGenerateReport={generateReport}
            />
          )}
        {/* 서버 정보 표시 */}
        {!loading &&
          !scanError &&
          scanMetadata &&
          scanMetadata.serverInfos &&
          scanMetadata.serverInfos.length > 0 && (
            <div className={styles.serverInfoSection}>
              <h3>Server Information:</h3>
              {scanMetadata.serverInfos.map((si, index) => (
                <div key={index} className={styles.serverInfoItem}>
                  <strong>Target: {si.target}</strong>
                  <ul>
                    {Object.entries(si.info).map(([key, value]) => (
                      <li key={key}>
                        <em>
                          {key
                            .replace(/_/g, " ")
                            .replace(/\b\w/g, (l) => l.toUpperCase())}
                          :
                        </em>{" "}
                        {String(value)}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        {!loading && !scanError && Object.keys(results).length > 0 && (
          <ResultTable results={results} />
        )}
      </main>
    </div>
  );
}

export default App;
