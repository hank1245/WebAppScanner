import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const scanWebsite = async (targetUrl, mode) => {
  const payload = {
    target_url: targetUrl,
    mode: mode,
  };
  const response = await axios.post(`${API_BASE_URL}/scan`, payload);
  return response.data.result;
};
