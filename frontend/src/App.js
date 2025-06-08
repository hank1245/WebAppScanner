import React from "react";
import styles from "./styles/App.module.css";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";
import LoadingSpinner from "./components/LoadingSpinner";
import ScanSummary from "./components/ScanSummary";
import Header from "./components/Header"; // Added
import Footer from "./components/Footer"; // Added
import FormSection from "./components/FormSection"; // Added
import { useScan } from "./hooks/useScan";
import { useReportGenerator } from "./hooks/useReportGenerator";

function App() {
  const {
    results,
    loading,
    scanMetadata,
    rawScanData, // Kept for useReportGenerator
    handleScan,
    getScanSummary,
    scanError, // Kept for error display
  } = useScan();

  const { generateReport } = useReportGenerator(
    results,
    scanMetadata,
    rawScanData // Kept rawScanData
  );

  const scanSummary = getScanSummary(); // Renamed from scanSummaryData

  return (
    <div className={styles.container}>
      <Header />

      <main>
        {" "}
        {/* Added main tag for semantic structure, can be styled if needed */}
        <FormSection
          title="Scan Configuration"
          description="Configure the options below and start scanning."
        >
          <ScanForm onScan={handleScan} isLoading={loading} />{" "}
          {/* Kept isLoading prop */}
        </FormSection>
        {loading && (
          <LoadingSpinner message="Scanning in progress. Please wait..." />
        )}{" "}
        {/* Added message prop */}
        {scanError && <div className={styles.errorMessage}>{scanError}</div>}
        {!loading && !scanError && (
          <>
            {scanSummary &&
              Object.keys(scanSummary).length > 0 && ( // Check if scanSummary has content
                <ScanSummary
                  summary={scanSummary} // Changed prop name from scanSummary to summary
                  onGenerateReport={generateReport}
                />
              )}

            {/* Server Information Section - Retained */}
            {scanMetadata &&
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

            {Object.keys(results).length > 0 && (
              <FormSection
                title="Scan Results"
                description="List of discovered directories (Status codes 200, 403)"
              >
                <ResultTable results={results} />
              </FormSection>
            )}
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
