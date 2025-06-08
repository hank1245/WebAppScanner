// JS 파일 내 API 엔드포인트 경로
console.log("Main JS script loaded.");

// API 호출 예시
fetch("/api/v1/users")
  .then((response) => response.json())
  .then((data) => console.log("Users:", data));

const itemUrl = "/api/v1/items?id=1";
fetch(itemUrl);

// 변수에 저장된 API 경로
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
