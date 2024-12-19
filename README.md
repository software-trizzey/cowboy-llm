# Cowboy LLM Chat Interface

A web-based chat interface that lets you interact with a cowboy-themed AI assistant named Hawthorne. The application supports both regular chat conversations and PDF document analysis.

## Features

- 🤠 Chat with a cowboy-themed AI assistant
- 📄 Upload and analyze PDF documents
- 🔍 Web search integration via Brave Search API
- 💬 Persistent chat sessions
- 🎨 Clean, responsive UI with markdown and code syntax highlighting

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.10 or higher
- [Ollama](https://ollama.ai) - for running the local LLM
- Docker (optional, for containerized deployment)

## Setup

1. Clone the repository: 
```bash
git clone https://github.com/software-trizzey/local-chat.git
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate # On Windows, use .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

5. Configure your environment variables in `.env`:
```bash
SERVICE_PORT=7860
SERVICE_HOST=0.0.0.0
CLIENT_HOST=localhost
BRAVE_API_KEY=your_brave_api_key # Optional, for web search functionality
```

6. Pull the Cowboy LLM model using Ollama:
```bash
ollama pull cowboyllm:latest
```

## Running the Application

### Local Development

1. Start the FastAPI server:
```bash
python src/main.py
```

2. Access the application in your browser at `http://localhost:7860`.

### Docker

1. Build the Docker image:
```bash
docker build -t local-chat .
```

2. Run the Docker container:
```bash
docker run -d -p 7860:7860 local-chat
```

3. Run with docker compose:
```bash
docker compose up -d
```

4. Access the application in your browser at `http://localhost:7860`.

## Usage

1. **Regular Chat**: Simply type your message in the input field and press Enter to chat with Hawthorne.

2. **PDF Analysis**: Click the paperclip icon to upload a PDF document (max 10MB). Hawthorne will analyze the document and provide a summary or answer questions about its contents.

3. **Web Search**: Include terms like "search", "look up", or "what is" in your message to trigger web search functionality (requires Brave API key).

## License

[MIT License](LICENSE)