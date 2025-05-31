import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000"; // 'backend'를 'localhost'로 변경

export const scanWebsite = async (
  targetUrls,
  mode,
  exclusions,
  maxDepth,
  respectRobotsTxt,
  dictionaryOperations,
  useDefaultDictionary,
  username, // Added username
  password // Added password
) => {
  const payload = {
    target_urls: targetUrls,
    mode: mode,
    exclusions: exclusions || [],
    max_depth: maxDepth,
    respect_robots_txt: respectRobotsTxt,
    dictionary_operations: dictionaryOperations || [],
    use_default_dictionary: useDefaultDictionary,
    username: username || null, // Add username to payload
    password: password || null, // Add password to payload
  };
  const response = await axios.post(`${API_BASE_URL}/scan`, payload);
  return response.data.result;
};

// 기본 딕셔너리 목록 가져오기 (프론트엔드 상수로 정의)
export const getDefaultDictionary = () => [
  "admin/",
  "backup/",
  "test/",
  "dev/",
  "old/",
  "logs/",
  "tmp/",
  "temp/",
  "public/",
  "uploads/",
  "files/",
  "downloads/",
  "data/",
  "config/",
  "private/",
  "web/",
  "new/",
  "archive/",
  ".git/",
  ".env/",
  ".svn/",
  ".htaccess/",
  ".htpasswd/",
  ".vscode/",
  ".idea/",
  "node_modules/",
  "vendor/",
  "build/",
  "dist/",
  "out/",
  "db/",
  "sql/",
  "credentials/",
];
