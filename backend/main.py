from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scanner import MultiWebScanner
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 기본 딕셔너리 목록을 상수로 정의
DEFAULT_DICTIONARY = [
    "admin/", "backup/", "test/", "dev/", "old/", "logs/", "tmp/", "temp/",
    "public/", "uploads/", "files/", "downloads/", "data/", "config/",
    "private/", "web/", "new/", "archive/", ".git/", ".env/", ".svn/",
    ".htaccess/", ".htpasswd/", ".vscode/", ".idea/", "node_modules/",
    "vendor/", "build/", "dist/", "out/", "db/", "sql/", "credentials/"
]

class DictionaryOperation(BaseModel):
    type: str  # "add" 또는 "remove"
    paths: List[str]

class ScanRequest(BaseModel):
    target_urls: List[str]
    mode: str = 'normal'
    dictionary_operations: Optional[List[DictionaryOperation]] = None
    use_default_dictionary: bool = True  # 기본 딕셔너리 사용 여부
    exclusions: list[str] = []
    max_depth: int = 2
    respect_robots_txt: bool = True

@app.post("/scan")
async def scan(request: ScanRequest):
    all_results = {}
    
    # 딕셔너리 목록 생성
    final_dictionary = []
    
    # 기본 딕셔너리 사용이 활성화된 경우 추가
    if request.use_default_dictionary:
        final_dictionary.extend(DEFAULT_DICTIONARY)
    
    # 사용자 정의 딕셔너리 작업 처리
    if request.dictionary_operations:
        for operation in request.dictionary_operations:
            if operation.type == "add":
                # 추가 작업의 경우 paths의 항목들을 딕셔너리에 추가
                for path in operation.paths:
                    if path and path not in final_dictionary:  # 중복 방지
                        final_dictionary.append(path)
            elif operation.type == "remove":
                # 제거 작업의 경우 paths의 항목들을 딕셔너리에서 제거
                final_dictionary = [p for p in final_dictionary if p not in operation.paths]
    
    # 빈 딕셔너리인 경우 기본값 사용
    if not final_dictionary:
        final_dictionary = DEFAULT_DICTIONARY
    
    try:
        for target_url_item in request.target_urls:
            scanner = MultiWebScanner(
                target_url=target_url_item,
                dictionary=final_dictionary,  # 최종 딕셔너리 전달
                mode=request.mode,
                exclusions=request.exclusions,
                respect_robots_txt=request.respect_robots_txt
            )
            result_item = scanner.run(max_depth=request.max_depth)
            all_results.update(result_item)
        
        return {"result": all_results}
    except Exception as e:
        print(f"Error during scan process: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during scanning: {str(e)}")
