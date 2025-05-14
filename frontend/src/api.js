import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const scanWebsite = async (
  targetUrls,
  mode,
  exclusions,
  maxDepth,
  respectRobotsTxt
) => {
  const payload = {
    target_urls: targetUrls,
    mode: mode,
    exclusions: exclusions || [],
    max_depth: maxDepth,
    respect_robots_txt: respectRobotsTxt, // 추가: robots.txt 준수 여부
  };
  const response = await axios.post(`${API_BASE_URL}/scan`, payload);
  return response.data.result;
};
