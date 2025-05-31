import { useState } from "react";
import { scanWebsite } from "../api";

export const useScan = () => {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [scanMetadata, setScanMetadata] = useState(null);
  const [rawScanData, setRawScanData] = useState(null);
  const [scanError, setScanError] = useState(null); // 에러 상태 추가

  const handleScan = async (
    targetUrlList,
    mode,
    exclusions,
    maxDepth,
    respectRobotsTxt,
    dictionaryOperations,
    useDefaultDictionary,
    sessionCookies
  ) => {
    setLoading(true);
    setResults({});
    setRawScanData(null);
    setScanError(null); // 새 스캔 시작 시 에러 초기화
    const startTime = new Date();

    let initialScanMetadata = {
      targets: targetUrlList,
      exclusions: exclusions,
      max_depth: maxDepth,
      respect_robots_txt: respectRobotsTxt,
      startTime: startTime,
      endTime: null,
      useDefaultDictionary: useDefaultDictionary,
      dictionaryOperations: dictionaryOperations,
      sessionCookiesProvided: !!sessionCookies, // ADDED
      serverInfos: [],
    };
    setScanMetadata(initialScanMetadata);

    try {
      const apiResponse = await scanWebsite(
        targetUrlList,
        mode,
        exclusions,
        maxDepth,
        respectRobotsTxt,
        dictionaryOperations,
        useDefaultDictionary,
        sessionCookies // ADDED
      );

      // apiResponse is now e.g., { "target1": {"directories": d1, "server_info": s1}, "target2": ... }
      setRawScanData(apiResponse);

      let mergedDirectories = {};
      const serverInfosList = [];

      Object.entries(apiResponse).forEach(([targetUrl, data]) => {
        if (data.directories) {
          mergedDirectories = { ...mergedDirectories, ...data.directories };
        }
        if (data.server_info) {
          serverInfosList.push({ target: targetUrl, info: data.server_info });
        }
      });

      setResults(mergedDirectories); // For ResultTable
      setScanMetadata((prev) => ({
        ...prev,
        endTime: new Date(),
        serverInfos: serverInfosList,
      }));
    } catch (error) {
      console.error("Error occurred during scan:", error);
      let errorMessage =
        "An unexpected error occurred during the scan. Please try again.";
      if (error.response && error.response.data) {
        // FastAPI validation errors or custom detail from HTTPException
        if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          // FastAPI validation error format
          errorMessage = error.response.data.detail
            .map((d) => `${d.loc.join(".")} - ${d.msg}`)
            .join("; ");
        } else if (error.response.data.error) {
          // 이전 custom error 형식 (호환성)
          errorMessage = error.response.data.error;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      setScanError(errorMessage);
      setResults({});
      setScanMetadata((prev) => ({ ...prev, endTime: new Date() }));
    } finally {
      setLoading(false);
    }
  };

  const getScanSummary = () => {
    if (!results || !scanMetadata || !scanMetadata.endTime) return null;

    // successfulEntries should be calculated based on the 'results' state (mergedDirectories)
    const successfulEntries = Object.entries(results).filter(
      ([_, info]) =>
        info &&
        (String(info.status_code) === "200" ||
          String(info.status_code) === "403")
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

  return {
    results,
    loading,
    scanMetadata,
    rawScanData,
    handleScan,
    getScanSummary,
    scanError,
  }; // scanError 반환
};
