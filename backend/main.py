from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scanner import MultiWebScanner
from fastapi.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    target_urls: List[str]
    mode: str = 'normal'
    dictionary: list[str] = [
        "admin/", "backup/", "test/", "dev/", "old/", "logs/", "tmp/", "temp/",
        "public/", "uploads/", "files/", "downloads/", "data/", "config/",
        "private/", "web/", "new/", "archive/", ".git/", ".env/", ".svn/",
        ".htaccess/", ".htpasswd/", ".vscode/", ".idea/", "node_modules/",
        "vendor/", "build/", "dist/", "out/", "db/", "sql/", "credentials/"
    ]
    exclusions: list[str] = []
    max_depth: int = 2

@app.post("/scan")
async def scan(request: ScanRequest):
    all_results = {}
    try:
        for target_url_item in request.target_urls:
            scanner = MultiWebScanner(
                target_url=target_url_item,
                dictionary=request.dictionary,
                mode=request.mode,
                exclusions=request.exclusions
            )
            result_item = scanner.run(max_depth=request.max_depth)
            all_results.update(result_item)
        
        return {"result": all_results}
    except Exception as e:
        print(f"Error during scan process: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during scanning: {str(e)}")
