from .spotify import play_work_playlist

def handle_work_mode(user_confirmation: str) -> str:
    """
    Handle the user's response to the work playlist suggestion
    """
    if user_confirmation.lower() in ['yes', 'sure', 'okay', 'yep', 'yeah', 'y']:
        success = play_work_playlist()
        if success:
            return "Alright partner! I've started your work playlist. Let me know if you need anything else!"
        else:
            return ("Whoops! Had some trouble starting the playlist. "
                   "You might need to start Spotify manually!")
    else:
        return "No problem! Let me know if you change your mind about that playlist. What else can I help you with?" 