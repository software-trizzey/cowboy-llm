import json
import os
import ollama
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

async def search_brave(query: str) -> Optional[str]:
    """Perform a web search using Brave Search API."""
    if not BRAVE_API_KEY:
        return "Error: Brave Search API key not configured"
    
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    
    params = {
        "q": query,
        "count": 3  # Number of results to return
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(BRAVE_API_URL, headers=headers, params=params)
            if response.status_code == 200:
                results = response.json()
                # Format the search results
                formatted_results = []
                for result in results.get("web", {}).get("results", []):
                    formatted_results.append(f"Title: {result['title']}\nURL: {result['url']}\nDescription: {result['description']}\n")
                return "\n".join(formatted_results)
            else:
                return f"Search failed with status code: {response.status_code}"
    except Exception as e:
        return f"Search error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    async def generate_response():
        try:
            # Check if we need to search
            if "search" in message.lower() or "look up" in message.lower() or "find" in message.lower() or "get latest" in message.lower():
                yield f"data: {json.dumps({'content': 'Searching the web...'})}\n\n"
                search_results = await search_brave(message)
                enhanced_prompt = f"""Context from web search:
{search_results}

Original question: {message}

Please provide a response based on the search results above."""
            else:
                enhanced_prompt = message

            stream = ollama.chat(
                model='llama3.2:latest',
                messages=[{"role": "user", "content": enhanced_prompt}],
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield f"data: {json.dumps({'content': chunk['message']['content']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'content': f'Error: {str(e)}'})}\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 