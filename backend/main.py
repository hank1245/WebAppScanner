import sys # sys 모듈 임포트
import traceback # traceback 모듈 임포트
from fastapi import FastAPI, HTTPException # HTTPException 임포트
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
    "vendor/", "build/", "dist/", "out/", "db/", "sql/", "credentials/", "secret/", "static/", 
    ".well-known/",
    ".well-known/security.txt",
]

class DictionaryOperation(BaseModel):
    type: str  # "add" 또는 "remove"
    paths: List[str]

class ScanRequest(BaseModel):
    target_urls: List[str]
    mode: str = 'normal'
    dictionary_operations: Optional[List[DictionaryOperation]] = None
    use_default_dictionary: bool = True
    exclusions: list[str] = []
    max_depth: int = 2
    respect_robots_txt: bool = True
    session_cookies_string: Optional[str] = None # ADDED

@app.post("/scan")
async def scan(request: ScanRequest):
    all_results_by_target = {} 

    # 딕셔너리 준비
    final_dictionary = []
    if request.use_default_dictionary:
        final_dictionary.extend(DEFAULT_DICTIONARY)
    
    if request.dictionary_operations:
        current_dict_set = set(final_dictionary)
        for op in request.dictionary_operations:
            if op.type == "add":
                for path in op.paths:
                    current_dict_set.add(path)
            elif op.type == "remove":
                for path in op.paths:
                    current_dict_set.discard(path)
        final_dictionary = sorted(list(current_dict_set))
    
    # 빈 딕셔너리인 경우 기본값 사용 (이중 확인)
    if not final_dictionary:
        final_dictionary = DEFAULT_DICTIONARY
    
    try:
        for target_url_item in request.target_urls:
            scanner = MultiWebScanner(
                target_url=target_url_item,
                dictionary=final_dictionary,
                mode=request.mode,
                exclusions=request.exclusions,
                respect_robots_txt=request.respect_robots_txt,
                session_cookies_string=request.session_cookies_string # ADDED
            )
            # scanner.run() now returns a dict: {"directories": {...}, "server_info": {...}}
            result_item_data = scanner.run(max_depth=request.max_depth)
            all_results_by_target[target_url_item] = result_item_data
        
        return {"result": all_results_by_target}
    except HTTPException as http_exc: # 이미 HTTPException인 경우 그대로 전달
        raise http_exc
    except Exception as e:
        print(f"Critical error during scan process for request {request.target_urls}: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Scan failed due to an internal server error. Error: {str(e)}. Check backend logs for more details.")
