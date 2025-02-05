from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import asyncio
import json
from typing import Optional

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class PaperResponse(BaseModel):
    papers: dict
    finish: bool

PAPER_API = "https://pasa-agent.ai/paper-agent/api/v1"
BATCH_SIZE = 50  # Number of papers to fetch in first batch
POLL_INTERVAL = 2  # Seconds between polls

async def fetch_papers(session_id: str) -> dict:
    """Fetch paper results from the API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PAPER_API}/single_get_result",
                json={"session_id": session_id}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error fetching papers: {str(e)}")

@app.post("/api/papers/search")
async def search_papers(request: SearchRequest):
    """Initialize paper search."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{PAPER_API}/single_paper_agent",
                json={
                    "user_query": request.query,
                    "session_id": request.session_id
                }
            )
            response.raise_for_status()
            return {"message": "Search initiated", "session_id": request.session_id}
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Error starting search: {str(e)}")

@app.post("/api/papers/results/{session_id}")
async def get_results(session_id: str):
    """Get paper results with batching."""
    try:
        response = await fetch_papers(session_id)
        
        if not response.get("papers"):
            return PaperResponse(papers={}, finish=False)

        papers = json.loads(response["papers"])
        paper_list = list(papers.values())
        total_papers = len(paper_list)
        
        # Sort papers by score
        paper_list.sort(key=lambda x: float(x["score"]), reverse=True)
        
        # Return first batch immediately if available
        result_papers = {}
        batch_size = min(BATCH_SIZE, total_papers)
        for i in range(batch_size):
            result_papers[str(i)] = paper_list[i]
        
        # If we have more papers and this isn't the final result,
        # include additional papers in pairs
        if total_papers > BATCH_SIZE and not response["finish"]:
            for i in range(BATCH_SIZE, total_papers, 2):
                if i + 1 < total_papers:
                    result_papers[str(i)] = paper_list[i]
                    result_papers[str(i + 1)] = paper_list[i + 1]
                else:
                    result_papers[str(i)] = paper_list[i]

        return PaperResponse(
            papers=result_papers,
            finish=response["finish"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing results: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
