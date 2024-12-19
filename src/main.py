import json
import os
import ollama
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Cookie

load_dotenv()

app = FastAPI()

SERVICE_PORT = int(os.getenv("SERVICE_PORT", 7860))
SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
CLIENT_HOST = os.getenv("CLIENT_HOST", "localhost")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{SERVICE_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

CHAT_HISTORIES = {}

async def search_brave(query: str) -> Optional[str]:
    """Perform a web search using Brave Search API."""
    if not BRAVE_API_KEY:
        return "Error: Brave Search API key not configured"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                BRAVE_API_URL,
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": BRAVE_API_KEY
                },
                params={
                    "q": query,
                    "count": 3
                }
            )
            
            if response.status_code == 200:
                results = response.json()
                formatted_results = []
                for result in results.get("web", {}).get("results", []):
                    formatted_results.append(
                        f"Source: {result['title']}\n"
                        f"URL: {result['url']}\n"
                        f"Summary: {result['description']}\n"
                    )
                return "\n---\n".join(formatted_results)
            else:
                return f"Search failed with status code: {response.status_code}"
    except Exception as e:
        return f"Search error: {str(e)}"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "chat.html",
        {
            "request": request,
            "port": SERVICE_PORT,
            "host": CLIENT_HOST
        }
    )

@app.post("/chat")
async def chat(message: str = Form(...), session_id: str = Cookie(None)):
    if session_id not in CHAT_HISTORIES:
        CHAT_HISTORIES[session_id] = {}

    chat_history = CHAT_HISTORIES[session_id].setdefault('messages', [])
    user_name = CHAT_HISTORIES[session_id].get('user_name', 'partner')

    # Update name detection to be more flexible
    name_indicators = ["my name is", "i'm called", "i am called", "call me"]
    for indicator in name_indicators:
        if indicator in message.lower():
            user_name = message.lower().split(indicator)[-1].strip()
            CHAT_HISTORIES[session_id]['user_name'] = user_name
            break

    # Add the user's message to history
    chat_history.append({"role": "user", "content": message})

    async def generate_response():
        try:
            messages = []
            
            # Add system message if it's the first message
            if len(chat_history) == 1:
                messages.append({
                    "role": "system",
                    "content": f"The user's name is {user_name}. Remember to maintain your cowboy persona as Hawthorne."
                })

            # Add chat history
            for msg in chat_history[-4:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # Handle web searches
            if any(term in message.lower() for term in ["search", "look up", "find", "get latest", "what is", "tell me about"]):
                yield f"data: {json.dumps({'content': 'Hold your horses partner, let me search the web...'})}\n\n"
                search_results = await search_brave(message)
                
                # Create a specific prompt for handling search results
                search_prompt = {
                    "role": "system",
                    "content": (
                        "Here's what I found on the web, partner. Let me break it down for you:\n\n"
                        f"{search_results}\n\n"
                        "Please provide a helpful response based on this information while maintaining "
                        "your cowboy persona as Hawthorne. Summarize the key points and explain them clearly."
                    )
                }
                messages.append(search_prompt)
                
                # Add the original question again to ensure it's addressed
                messages.append({
                    "role": "user",
                    "content": f"Based on that search information, can you answer: {message}"
                })
            
            stream = ollama.chat(
                model='cowboyllm:latest',
                messages=messages,
                stream=True,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )
            
            response_content = ""
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    response_content += content
                    yield f"data: {json.dumps({'content': content})}\n\n"

            # Store the complete response in chat history
            chat_history.append({"role": "assistant", "content": response_content})

        except Exception as e:
            error_message = f"Whoa there partner, we've hit a snag: {str(e)}"
            yield f"data: {json.dumps({'content': error_message})}\n\n"
            chat_history.append({"role": "assistant", "content": error_message})

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT) 