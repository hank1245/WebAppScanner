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
    use_default_dictionary: bool = True
    exclusions: list[str] = []
    max_depth: int = 2
    respect_robots_txt: bool = True
    session_cookies_string: Optional[str] = None # ADDED

@app.post("/scan")
async def scan(request: ScanRequest):
    all_results_by_target = {} # Changed to store results per target

    # 딕셔너리 준비
    final_dictionary = []
    if request.use_default_dictionary:
        final_dictionary.extend(DEFAULT_DICTIONARY)
    
    if request.dictionary_operations:
        current_dict_set = set(final_dictionary)
        for op in request.dictionary_operations:
            if op.action == "add":
                current_dict_set.add(op.item)
            elif op.action == "remove":
                current_dict_set.discard(op.item)
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
        
        return {"result": all_results_by_target} # Return results keyed by target URL
    except Exception as e:
        print(f"Error during scan process: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during scanning: {str(e)}")
