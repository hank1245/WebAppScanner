import React, { useState } from "react";
import { scanWebsite } from "./api";
import ScanForm from "./components/ScanForm";
import ResultTable from "./components/ResultTable";
import "./App.css"; // 기본 CSS 파일 사용

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
    dictionaryOperations, // 추가: 딕셔너리 작업
    useDefaultDictionary // 추가: 기본 딕셔너리 사용 여부
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
      // 딕셔너리 관련 메타데이터 추가
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
      console.error("스캔 중 오류 발생:", error);
      alert("스캔에 실패했습니다.");
      setScanMetadata((prev) => ({ ...prev, endTime: new Date() }));
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
      // 리포트에 딕셔너리 설정 정보 추가
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
        <h1>📁 디렉토리 스캐너</h1>
        <p className="app-description">
          웹사이트 디렉토리를 탐색하고 숨겨진 경로를 검색하는 도구입니다.
        </p>
      </header>

      <div className="card">
        <div className="card-header">
          <h2>스캔 설정</h2>
          <p>아래 옵션을 설정하고 스캔을 시작하세요.</p>
        </div>
        <div className="card-body">
          <ScanForm onScan={handleScan} />
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loader"></div>
          <p>스캔 중입니다. 잠시만 기다려주세요...</p>
        </div>
      ) : (
        <>
          {scanSummary && (
            <div className="card scan-summary">
              <div className="card-header">
                <h2>스캔 결과 요약</h2>
              </div>
              <div className="card-body">
                <div className="summary-grid">
                  <div className="summary-item">
                    <span className="summary-label">스캔 대상 수</span>
                    <span className="summary-value">{scanSummary.targets}</span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">검사한 경로 수</span>
                    <span className="summary-value">
                      {scanSummary.totalPaths}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">발견된 디렉토리 수</span>
                    <span className="summary-value">
                      {scanSummary.successfulPaths}
                    </span>
                  </div>
                  <div className="summary-item">
                    <span className="summary-label">소요 시간</span>
                    <span className="summary-value">
                      {scanSummary.duration}초
                    </span>
                  </div>
                </div>

                <button onClick={generateReport} className="btn btn-primary">
                  <span className="icon">📊</span> 상세 리포트 다운로드
                </button>
              </div>
            </div>
          )}

          {Object.keys(results).length > 0 && (
            <div className="card">
              <div className="card-header">
                <h2>스캔 결과 목록</h2>
                <p>발견된 디렉토리 목록입니다 (상태 코드 200, 403)</p>
              </div>
              <div className="card-body">
                <ResultTable results={results} />
              </div>
            </div>
          )}
        </>
      )}

      <footer className="app-footer">
        <p>
          © 디렉토리 스캐너 by Hank Kim | 타겟 웹사이트에서 스캔 수행 시 법적
          권한이 필요한지 확인하세요. 법적인 문제 발생시 개발자에게 책임이
          없습니다.
        </p>
      </footer>
    </div>
  );
}

export default App;
