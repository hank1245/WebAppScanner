import { useState } from "react";
import { scanWebsite } from "../api";

export const useScan = () => {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [scanMetadata, setScanMetadata] = useState(null);
  const [rawScanData, setRawScanData] = useState(null);
  const [scanError, setScanError] = useState(null);

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
    setScanError(null);
    const startTime = new Date();

    let initialScanMetadata = {
      targets: targetUrlList,
      exclusions: exclusions,
      max_depth: maxDepth,
      respect_robots_txt: respectRobotsTxt,
      startTime: startTime,
      sessionCookiesProvided: !!sessionCookies,
      useDefaultDictionary: useDefaultDictionary,
      dictionaryOperations: dictionaryOperations,
    };
    setScanMetadata(initialScanMetadata);

    try {
      const rawResults = await scanWebsite(
        targetUrlList,
        mode,
        exclusions,
        maxDepth,
        respectRobotsTxt,
        dictionaryOperations,
        useDefaultDictionary,
        sessionCookies
      );

      setRawScanData(rawResults);

      const mergedDirectories = {};
      const serverInfosList = {};

      Object.entries(rawResults).forEach(([targetUrl, result]) => {
        if (result && result.directories) {
          Object.assign(mergedDirectories, result.directories);
        }
        if (result && result.server_info) {
          serverInfosList[targetUrl] = result.server_info;
        }
      });

      setResults(mergedDirectories);
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
        if (typeof error.response.data.detail === "string") {
          errorMessage = error.response.data.detail;
        } else if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail
            .map((d) => `${d.loc.join(".")} - ${d.msg}`)
            .join("; ");
        } else if (error.response.data.error) {
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

    const allEntries = Object.entries(results);

    const successfulDirEntries = allEntries.filter(
      ([_, info]) =>
        info &&
        (String(info.status_code) === "200" ||
          String(info.status_code) === "403") &&
        info.source !== "js_api"
    );

    const foundApiEndpoints = allEntries.filter(
      ([_, info]) =>
        info &&
        info.source === "js_api" &&
        (String(info.status_code) === "200" ||
          String(info.status_code) === "403")
    );

    const duration =
      (scanMetadata.endTime.getTime() - scanMetadata.startTime.getTime()) /
      1000;

    return {
      duration: duration.toFixed(2),
      totalPaths: allEntries.length,
      successfulPaths: successfulDirEntries.length,
      foundApiEndpoints: foundApiEndpoints.length,
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
  };
};
