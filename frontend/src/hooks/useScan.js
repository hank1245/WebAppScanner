import { useState } from "react";
import { scanWebsite } from "../api";

export const useScan = () => {
  const [results, setResults] = useState({}); // This will store merged directories for ResultTable
  const [loading, setLoading] = useState(false);
  const [scanMetadata, setScanMetadata] = useState(null);
  const [rawScanData, setRawScanData] = useState(null); // To store the full API response

  const handleScan = async (
    targetUrlList,
    mode,
    exclusions,
    maxDepth,
    respectRobotsTxt,
    dictionaryOperations,
    useDefaultDictionary,
    sessionCookies // ADDED
  ) => {
    setLoading(true);
    setResults({});
    setRawScanData(null); // Reset raw data
    const startTime = new Date();
    // Initial metadata
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
      alert("Scan failed.");
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
    handleScan,
    getScanSummary,
  };
};
