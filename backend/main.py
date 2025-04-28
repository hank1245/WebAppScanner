from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from scanner import MultiWebScanner
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ScanRequest(BaseModel):
    target_url: str
    mode: str = 'normal'  # default = 'normal'
    dictionary: list[str] = ["admin", "backup", "config", "logs", "test", "phpmyadmin", "wp-admin"]

@app.post("/scan")
async def scan(request: ScanRequest):
    try:
        scanner = MultiWebScanner(
            target_url=request.target_url,
            dictionary=request.dictionary,
            mode=request.mode
        )
        result = scanner.run(max_depth=2)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
