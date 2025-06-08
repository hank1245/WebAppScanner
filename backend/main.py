import sys
import traceback
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

DEFAULT_DICTIONARY = [
    "admin/", "backup/", "test/", "dev/", "old/", "logs/", "tmp/", "temp/",
    "public/", "uploads/", "files/", "downloads/", "data/", "config/",
    "private/", "web/", "new/", "archive/", ".git/", ".env/", ".svn/",
    ".htaccess/", ".htpasswd/", ".vscode/", ".idea/", "node_modules/",
    "vendor/", "build/", "dist/", "out/", "db/", "sql/", "credentials/", "secret/", "static/", "hidden/",
    ".well-known/",
    ".well-known/security.txt",
    ".well-known/assetlinks.json",
    ".well-known/apple-app-site-association",
    ".well-known/change-password",
    ".well-known/dnt-policy.txt",
    ".well-known/host-meta",
    ".well-known/openid-configuration",
    ".well-known/jwks.json"
]

class DictionaryOperation(BaseModel):
    type: str
    paths: List[str]

class ScanRequest(BaseModel):
    target_urls: List[str]
    mode: str = 'normal'
    dictionary_operations: Optional[List[DictionaryOperation]] = None
    use_default_dictionary: bool = True
    exclusions: list[str] = []
    max_depth: int = 2
    respect_robots_txt: bool = True
    session_cookies_string: Optional[str] = None

@app.post("/scan")
async def scan(request: ScanRequest):
    all_results_by_target = {} 

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
                    if path in current_dict_set:
                        current_dict_set.remove(path)
        final_dictionary = list(current_dict_set)
    
    try:
        for target_url in request.target_urls:
            scanner = MultiWebScanner(
                target_url=target_url,
                dictionary=final_dictionary,
                mode=request.mode,
                exclusions=request.exclusions,
                respect_robots_txt=request.respect_robots_txt,
                session_cookies_string=request.session_cookies_string
            )
            
            result = scanner.run(max_depth=request.max_depth)
            all_results_by_target[target_url] = result

        return {"result": all_results_by_target}
    except Exception as e:
        error_msg = f"Scan failed: {str(e)}"
        error_traceback = traceback.format_exc()
        print(f"Error: {error_msg}\n{error_traceback}")
        raise HTTPException(status_code=500, detail=error_msg)
