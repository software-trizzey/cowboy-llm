import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SPOTIFY_SERVER_HOST = os.getenv("SPOTIFY_SERVER_HOST")
SPOTIFY_SERVER_PORT = os.getenv("SPOTIFY_SERVER_PORT")

def play_work_playlist():
    """
    Play work playlist by making request to host server
    """
    LOGGER.info("Requesting work playlist from host server")
    try:
        response = httpx.post(f"http://{SPOTIFY_SERVER_HOST}:{SPOTIFY_SERVER_PORT}/spotify/play/work")
        if response.status_code == 200:
            return True
        LOGGER.error(f"Failed to play playlist: {response.text}")
        return False
    except Exception as e:
        LOGGER.error(f"Error communicating with host server: {e}")
        return False

def play_last_played_song():
    """This function can be implemented similarly if needed"""
    pass