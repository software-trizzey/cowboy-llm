# Cowboy LLM

<img src="https://github.com/user-attachments/assets/8c2dd846-bbe0-42a9-ac8e-1a4d5f4a0243" alt="cowboy-llm" width=620 />

A web-based chat interface that lets you interact with a cowboy-themed AI assistant named Hawthorne. The application supports both regular chat conversations and PDF document analysis.

## Features

- 🤠 Chat with a cowboy-themed AI assistant
- 📄 Upload and analyze PDF documents
- 🔍 Web search integration via Brave Search API
- 💬 Persistent chat sessions
- 🎨 Clean, responsive UI with markdown and code syntax highlighting
- 🎵 Spotify integration for work/focus mode

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.10 or higher
- [Ollama](https://ollama.ai) - for running the local LLM
- Docker (optional, for containerized deployment)

## Setup

1. Clone the repository: 
```bash
git clone https://github.com/software-trizzey/cowboy-llm
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
SPOTIFY_WORK_PLAYLIST_ID=your_playlist_id # Optional, for Spotify integration
SPOTIFY_SERVER_HOST=localhost
SPOTIFY_SERVER_PORT=7861
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
docker build -t cowboy-llm .
```

2. Run the Docker container:
```bash
docker run -d -p 7860:7860 cowboy-llm
```

3. Run with docker compose:
```bash
docker compose up -d
```

4. Access the application in your browser at `http://localhost:7860`.

## Spotify Integration

The application includes a feature to play a work/focus playlist through Spotify when users indicate they're trying to work or focus. To use this feature:

1. Set up the Spotify server:
```bash
# Start the Spotify server (in a separate terminal)
python src/spotify_server.py
```

2. Configure your work playlist:
- Get your playlist ID from Spotify (right-click playlist → Share → Copy link)
- Add the ID to your `.env` file as `SPOTIFY_WORK_PLAYLIST_ID`

The Spotify server runs on port 7861 by default and handles requests from the main application to control Spotify on your local machine.

## Usage

1. **Regular Chat**: Simply type your message in the input field and press Enter to chat with Hawthorne.

2. **PDF Analysis**: Click the paperclip icon to upload a PDF document (max 10MB). Hawthorne will analyze the document and provide a summary or answer questions about its contents.

3. **Web Search**: Include terms like "search", "look up", or "what is" in your message to trigger web search functionality (requires Brave API key).

4. **Work Mode**: Tell Hawthorne you're trying to work or need to focus, and he'll offer to play your work playlist through Spotify.

## License

[MIT License](LICENSE)
