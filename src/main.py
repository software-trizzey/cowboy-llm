import httpx
import os

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

OLLAMA_API_URL = "http://localhost:11434/api/generate"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat")
async def chat(message: str = Form(...)):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                OLLAMA_API_URL,
                json={
                    "model": "llama3.2:latest",
                    "prompt": message,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                return {"response": response.json()["response"]}
            else:
                error_msg = response.json() if response.status_code != 500 else str(response.status_code)
                print(f"Error response from Ollama: {error_msg}")
                return {"response": f"Error: Could not get response from Ollama. Status: {response.status_code}"}
                
        except httpx.ReadTimeout:
            return {"response": "Error: Request to Ollama timed out. Please try again."}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {"response": "Error: An unexpected error occurred"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 