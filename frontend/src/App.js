import React from "react";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";
import ScanSummary from "./components/ScanSummary";
import LoadingSpinner from "./components/LoadingSpinner";
import FormSection from "./components/FormSection";
import Header from "./components/Header";
import Footer from "./components/Footer";
import { useScan } from "./hooks/useScan";
import { useReportGenerator } from "./hooks/useReportGenerator";
import styles from "./styles/App.module.css";

function App() {
  const { results, loading, scanMetadata, handleScan, getScanSummary } =
    useScan();
  const { generateReport } = useReportGenerator(results, scanMetadata);
  const scanSummary = getScanSummary();

  return (
    <div className={styles.container}>
      <Header />

      <FormSection
        title="Scan Configuration"
        description="Configure the options below and start scanning."
      >
        <ScanForm onScan={handleScan} />
      </FormSection>

      {loading ? (
        <LoadingSpinner message="Scanning in progress. Please wait..." />
      ) : (
        <>
          <ScanSummary
            scanSummary={scanSummary}
            onGenerateReport={generateReport}
          />

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

      <Footer />
    </div>
  );
}

export default App;
