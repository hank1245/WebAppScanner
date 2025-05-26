import { useState } from "react";
import { scanWebsite } from "../api";

export const useScan = () => {
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

  return {
    results,
    loading,
    scanMetadata,
    handleScan,
    getScanSummary,
  };
};
