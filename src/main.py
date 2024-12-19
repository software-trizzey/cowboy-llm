import logging
import json
import os
import ollama
import httpx
from typing import Optional
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Cookie
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
import io

load_dotenv()

app = FastAPI()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB limit

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
async def chat(
    message: str = Form(...),
    file: UploadFile = File(None),
    session_id: str = Cookie(None)
):
    if session_id not in CHAT_HISTORIES:
        CHAT_HISTORIES[session_id] = {}

    chat_history = CHAT_HISTORIES[session_id].setdefault('messages', [])
    user_name = CHAT_HISTORIES[session_id].get('user_name', 'partner')

    # Handle PDF file if uploaded
    if file and file.filename.endswith('.pdf'):
        return await handle_pdf_upload(file, message, chat_history)

    # Update name detection to be more flexible
    name_indicators = ["my name is", "i'm called", "i am called", "call me"]
    for indicator in name_indicators:
        if indicator in message.lower():
            user_name = message.lower().split(indicator)[-1].strip()
            CHAT_HISTORIES[session_id]['user_name'] = user_name
            break

    # Handle regular chat messages (including web searches) as before
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

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "templates/static")), name="static")

def extract_text_from_pdf(file: UploadFile) -> str:
    """
    Extract text from a PDF file upload
    """
    try:
        # Read file content
        contents = file.file.read()
        
        # Check file size
        if len(contents) > MAX_PDF_SIZE:
            raise HTTPException(status_code=413, detail="PDF file too large")
            
        # Create PDF reader object
        pdf_reader = PdfReader(io.BytesIO(contents))
        
        if len(pdf_reader.pages) == 0:
            raise ValueError("PDF file is empty")
            
        # Extract text from all pages
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
            
        return text.strip()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    finally:
        file.file.close()

async def handle_pdf_upload(file: UploadFile, message: str = "", chat_history: list = None) -> StreamingResponse:
    """
    Centralized function to handle PDF uploads and generate responses
    """
    try:
        LOGGER.info(f"Starting PDF processing for file: {file.filename}")
        pdf_text = extract_text_from_pdf(file)
        
        if not pdf_text:
            return StreamingResponse(
                iter([f"data: {json.dumps({'content': 'No text could be extracted from the PDF'})}\n\n"]),
                media_type="text/event-stream"
            )

        # Simplify the prompt
        LOGGER.info("Creating prompt for model")
        messages = [
            {
                "role": "system",
                "content": "You are Hawthorne, a helpful cowboy assistant. Maintain your cowboy persona while providing accurate information."
            },
            {
                "role": "user",
                "content": f"Here's a document I'd like you to summarize:\n\n{pdf_text}\n\nPlease provide a clear summary of this document."
            }
        ]
        
        if message.strip():
            messages.append({"role": "user", "content": f"Additional instructions: {message}"})

        LOGGER.info(f"Sending {len(messages)} messages to model")

        async def generate_response():
            try:
                stream = ollama.chat(
                    model='cowboyllm:latest',
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 2048,  # Increase token limit
                        "timeout": 60  # Increase timeout
                    }
                )
                
                response_content = ""
                chunk_count = 0
                
                for chunk in stream:
                    chunk_count += 1
                    LOGGER.debug(f"Raw chunk {chunk_count}: {chunk}")  # Debug raw chunks
                    
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        if content.strip():
                            response_content += content
                            LOGGER.debug(f"Chunk {chunk_count}: {content[:50]}...")
                            yield f"data: {json.dumps({'content': content})}\n\n"
                    else:
                        LOGGER.error(f"Received invalid chunk format: {chunk}")

                LOGGER.info(f"Stream completed. Processed {chunk_count} chunks")
                if not response_content:
                    LOGGER.warning("Warning: No content was generated")
                    error_msg = "Sorry partner, I'm having trouble processing this document. Let me try a simpler approach."
                    yield f"data: {json.dumps({'content': error_msg})}\n\n"
                    
                    # Fallback to simpler prompt
                    try:
                        LOGGER.info("Attempting fallback response")
                        response = ollama.chat(
                            model='cowboyllm:latest',
                            messages=[{
                                "role": "user",
                                "content": f"Please summarize this text in a simple way: {pdf_text[:1000]}..."  # First 1000 chars
                            }],
                            options={
                                "temperature": 0.5,
                                "timeout": 30
                            }
                        )
                        if response and 'content' in response['message']:
                            yield f"data: {json.dumps({'content': response['message']['content']})}\n\n"
                    except Exception as e:
                        LOGGER.error(f"Fallback also failed: {str(e)}")
                    
                if chat_history is not None:
                    chat_history.append({
                        "role": "user", 
                        "content": f"[Uploaded PDF: {file.filename}]\n{message if message else 'Please summarize this document.'}"
                    })
                    if response_content:
                        chat_history.append({
                            "role": "assistant", 
                            "content": response_content
                        })

            except Exception as e:
                LOGGER.error(f"Error in generate_response: {str(e)}")
                error_message = f"Whoa there partner, we've hit a snag: {str(e)}"
                yield f"data: {json.dumps({'content': error_message})}\n\n"

        return StreamingResponse(
            generate_response(),
            media_type="text/event-stream"
        )

    except Exception as e:
        LOGGER.error(f"Error in handle_pdf_upload: {str(e)}")
        error_msg = str(e)
        if "PDF file is empty" in error_msg:
            error_msg = "The PDF appears to be empty. Please try a different document."
        elif "No text could be extracted" in error_msg:
            error_msg = "Could not extract text from this PDF. The document might be scanned or image-based."
        return StreamingResponse(
            iter([f"data: {json.dumps({'content': f'Error processing PDF: {error_msg}'})}\n\n"]),
            media_type="text/event-stream"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=SERVICE_HOST, port=SERVICE_PORT) 