import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const scanWebsite = async (targetUrls, mode, exclusions, maxDepth) => {
  // targetUrl -> targetUrls (array)
  const payload = {
    target_urls: targetUrls, // target_url -> target_urls
    mode: mode,
    exclusions: exclusions || [],
    max_depth: maxDepth,
  };
  const response = await axios.post(`${API_BASE_URL}/scan`, payload);
  return response.data.result;
};
