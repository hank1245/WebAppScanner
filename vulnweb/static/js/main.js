// JS 파일 내 API 엔드포인트 경로
console.log("Main JS script loaded.");

fetch("/api/v1/users")
  .then((response) => response.json())
  .then((data) => console.log("Users:", data));

const itemUrl = "/api/v1/items?id=1";
fetch(itemUrl);

const config = {
  apiBase: "/api/v2/",
  endpoints: {
    status: "status",
    health: "health",
  },
};

function checkStatus() {
  const url = config.apiBase + config.endpoints.status;
  console.log(`Checking status at: ${url}`);
}

checkStatus();
