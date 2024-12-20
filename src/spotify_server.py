import os
import logging
from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

WORK_PLAYLIST_ID = os.getenv("SPOTIFY_WORK_PLAYLIST_ID")
SPOTIFY_SERVER_HOST = os.getenv("SPOTIFY_SERVER_HOST")
SPOTIFY_SERVER_PORT = os.getenv("SPOTIFY_SERVER_PORT")

@app.post("/spotify/play/work")
async def play_work_playlist():
    """Play the work playlist on Spotify"""
    try:
        print(f"Playing work playlist: {WORK_PLAYLIST_ID}")
        script = f'''
        tell application "Spotify"
            play track "spotify:playlist:{WORK_PLAYLIST_ID}"
        end tell
        '''
        success = os.system(f'osascript -e \'{script}\'') == 0
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=500, detail="Failed to control Spotify")
    except Exception as e:
        LOGGER.error(f"Error controlling Spotify: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host=SPOTIFY_SERVER_HOST, port=int(SPOTIFY_SERVER_PORT)) 