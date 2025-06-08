import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export const scanWebsite = async (
  targetUrls,
  mode,
  exclusions,
  maxDepth,
  respectRobotsTxt,
  dictionaryOperations,
  useDefaultDictionary,
  sessionCookies
) => {
  const payload = {
    target_urls: targetUrls,
    mode: mode,
    exclusions: exclusions || [],
    max_depth: maxDepth,
    respect_robots_txt: respectRobotsTxt,
    dictionary_operations: dictionaryOperations || [],
    use_default_dictionary: useDefaultDictionary,
    session_cookies_string: sessionCookies || null,
  };
  const response = await axios.post(`${API_BASE_URL}/scan`, payload);
  return response.data.result;
};

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
  "secret/",
  "static/",
  "hidden/",
  ".well-known/",
  ".well-known/security.txt",
  ".well-known/assetlinks.json",
  ".well-known/apple-app-site-association",
  ".well-known/change-password",
  ".well-known/dnt-policy.txt",
  ".well-known/host-meta",
  ".well-known/openid-configuration",
  ".well-known/jwks.json",
];
