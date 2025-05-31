import { downloadJSON } from "../utils/fileUtils";

export const useReportGenerator = (results, scanMetadata) => {
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
      credentials_provided: scanMetadata.credentialsProvided, // 이미 반영됨
      exclusions_list: scanMetadata.exclusions,
      checked_paths_count: Object.keys(results).length,
      all_attempted_paths_details: Object.entries(results).map(
        ([url, info]) => ({
          // 이미 반영됨
          url: url,
          status_code: info ? String(info.status_code) : "UNKNOWN_ERROR",
          content_length: info ? info.content_length : 0,
          directory_listing: info ? info.directory_listing : false,
          note:
            info && info.note
              ? info.note
              : info
              ? "No specific note."
              : "Scan info missing.",
        })
      ),
      successful_directories_count: successfulEntries.length,
      successful_directories_list: successfulEntries.map(([url, info]) => ({
        url: url,
        status_code: info.status_code,
        content_length: info.content_length,
        directory_listing: info.directory_listing, // directory_listing 정보 추가
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

  return { generateReport };
};
