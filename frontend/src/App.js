import React, { useState } from "react";
import { scanWebsite } from "./api";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";
import ScanSummary from "./components/ScanSummary";
import LoadingSpinner from "./components/LoadingSpinner";
import FormSection from "./components/FormSection";
import "./App.css";

// Helper function to download JSON
const downloadJSON = (data, filename) => {
  const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(
    JSON.stringify(data, null, 2)
  )}`;
  const link = document.createElement("a");
  link.href = jsonString;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

function App() {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [scanMetadata, setScanMetadata] = useState(null);

  const handleScan = async (
    targetUrlList,
    mode,
    exclusions,
    maxDepth,
    respectRobotsTxt,
    dictionaryOperations,
    useDefaultDictionary
  ) => {
    setLoading(true);
    setResults({});
    const startTime = new Date();
    setScanMetadata({
      targets: targetUrlList,
      exclusions: exclusions,
      maxDepth: maxDepth,
      respectRobotsTxt: respectRobotsTxt,
      startTime: startTime,
      endTime: null,
      useDefaultDictionary: useDefaultDictionary,
      dictionaryOperations: dictionaryOperations,
    });

    try {
      const scanResult = await scanWebsite(
        targetUrlList,
        mode,
        exclusions,
        maxDepth,
        respectRobotsTxt,
        dictionaryOperations,
        useDefaultDictionary
      );
      setResults(scanResult);
      setScanMetadata((prev) => ({ ...prev, endTime: new Date() }));
    } catch (error) {
      console.error("Error occurred during scan:", error);
      alert("Scan failed.");
      setScanMetadata((prev) => ({ ...prev, endTime: new Date() }));
    } finally {
      setLoading(false);
    }
  };

  const generateReport = () => {
    if (!results || !scanMetadata || !scanMetadata.endTime) {
      alert("No data available to generate report.");
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
      respect_robots_txt: scanMetadata.respectRobotsTxt,
      exclusions_list: scanMetadata.exclusions,
      checked_paths_count: Object.keys(results).length,
      successful_directories_count: successfulEntries.length,
      successful_directories_list: successfulEntries.map(([url, info]) => ({
        url: url,
        status_code: info.status_code,
        content_length: info.content_length,
        directory_listing: info.directory_listing,
      })),
      dictionary_settings: {
        use_default_dictionary: scanMetadata.useDefaultDictionary,
        dictionary_operations: scanMetadata.dictionaryOperations,
      },
    };

    downloadJSON(
      reportData,
      `scan_report_${new Date().toISOString().split("T")[0]}.json`
    );
  };

  // 스캔 결과 요약 정보 계산
  const getScanSummary = () => {
    if (!results || !scanMetadata || !scanMetadata.endTime) return null;

    const successfulEntries = Object.entries(results).filter(
      ([_, info]) =>
        info && (info.status_code === 200 || info.status_code === 403)
    );

    const duration =
      (scanMetadata.endTime.getTime() - scanMetadata.startTime.getTime()) /
      1000;

    return {
      duration: duration.toFixed(2),
      totalPaths: Object.keys(results).length,
      successfulPaths: successfulEntries.length,
      targets: scanMetadata.targets.length,
    };
  };

  const scanSummary = getScanSummary();

  return (
    <div className="container">
      <header className="app-header">
        <h1>📁 Directory Scanner</h1>
        <p className="app-description">
          A tool for exploring website directories and discovering hidden paths.
        </p>
      </header>

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

      <footer className="app-footer">
        <p>
          © Directory Scanner by Hank Kim | Please ensure you have legal
          authorization before scanning target websites. The developer is not
          responsible for any legal issues that may arise.
        </p>
      </footer>
    </div>
  );
}

export default App;
