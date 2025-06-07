import { downloadJSON } from "../utils/fileUtils";

export const useReportGenerator = (results, scanMetadata, rawScanData) => {
  const generateReport = () => {
    if (!results || !scanMetadata || !scanMetadata.endTime) {
      alert("Scan data is not complete yet.");
      return;
    }

    const allEntries = Object.entries(results);

    const successfulDirEntries = allEntries.filter(
      ([_, info]) =>
        info &&
        (String(info.status_code) === "200" ||
          String(info.status_code) === "403") &&
        info.source !== "js_api"
    );

    const foundApiEndpointsList = allEntries.filter(
      ([_, info]) =>
        info &&
        info.source === "js_api" &&
        (String(info.status_code) === "200" ||
          String(info.status_code) === "403")
    );

    const attemptedApiPathsList = allEntries.filter(
      ([_, info]) => info && info.source === "js_api"
    );

    const duration =
      (scanMetadata.endTime.getTime() - scanMetadata.startTime.getTime()) /
      1000;

    const reportData = {
      scan_metadata: {
        targets: scanMetadata.targets,
        scan_start_time: scanMetadata.startTime.toISOString(),
        scan_end_time: scanMetadata.endTime.toISOString(),
        scan_duration_seconds: parseFloat(duration.toFixed(2)),
        max_crawling_depth: scanMetadata.max_depth,
        respect_robots_txt: scanMetadata.respect_robots_txt,
        exclusions_used: scanMetadata.exclusions,
        session_cookies_provided: scanMetadata.sessionCookiesProvided,
        dictionary_settings: {
          // 사전 설정 추가
          use_default_dictionary: scanMetadata.useDefaultDictionary,
          dictionary_operations: scanMetadata.dictionaryOperations,
        },
        server_information: scanMetadata.serverInfos, // 서버 정보 추가
      },
      summary: {
        total_targets_scanned: scanMetadata.targets.length,
        total_paths_attempted: allEntries.length,
        successful_directories_found: successfulDirEntries.length,
        responsive_api_endpoints_found: foundApiEndpointsList.length, // JS API 중 200/403
        total_js_api_paths_attempted: attemptedApiPathsList.length, // JS API 모든 시도
      },
      all_attempted_paths_details: allEntries.map(([url, info]) => ({
        url: url,
        status_code: info ? String(info.status_code) : "UNKNOWN_ERROR",
        content_length: info ? info.content_length : 0,
        directory_listing: info ? info.directory_listing : false,
        source: info ? info.source || "unknown" : "unknown", // source 정보 추가
        note:
          info && info.note
            ? info.note
            : info
            ? "No specific note."
            : "Scan info missing.",
      })),
      successful_directories_list: successfulDirEntries.map(([url, info]) => ({
        url: url,
        status_code: info.status_code,
        content_length: info.content_length,
        directory_listing: info.directory_listing,
        source: info.source || "unknown",
        note: info.note || "Path found.",
      })),
      responsive_api_endpoints_list: foundApiEndpointsList.map(
        ([url, info]) => ({
          url: url,
          status_code: info.status_code,
          content_length: info.content_length,
          source: info.source, // 항상 'js_api'
          note: info.note || "API Endpoint responded.",
        })
      ),
    };

    downloadJSON(
      reportData,
      `directory_tracer_report_${new Date().toISOString().split("T")[0]}.json`
    );
  };

  return { generateReport };
};
