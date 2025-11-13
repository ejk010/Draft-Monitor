import requests
import os
from bs4 import BeautifulSoup
from dateutil.parser import parse
from dateutil.tz import gettz
import datetime
import re 

# --- Configuration ---
LEAGUE_URL = "https://www.pennantchase.com/league/baseball/home?lgid=691"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
STATUS_FILE = "last_status.txt"

# --- REQUIRED: EDIT THIS MAP ---
# Map the owner handle (from the website) to the Discord Role ID or User ID.
# Use this format for a Role ID: <@&ROLE_ID>
# Use this format for a User ID: <@USER_ID>
DISCORD_ID_MAP = {
    # EXAMPLE: Replace "bigdaddybrett05" with the actual handle for the current team owner
    "bigdaddybrett05": "<@&123456789012345678>", 
    "WhiteSoxOwnerHandle": "<@&987654321098765432>", 
}
# --- End Configuration ---


def get_draft_status():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"}
        r = requests.get(LEAGUE_URL, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, 'html.parser')
        status_div = soup.find("div", {"class": "alert-info"})
        
        if status_div:
            full_text = status_div.get_text(strip=True)
            
            # --- Start of logic ---
            start_marker = "is currently open."
            end_marker = "Note, auto picks"
            
            start_index = full_text.find(start_marker)
            end_index = full_text.find(end_marker)
            
            if start_index == -1 or end_index == -1:
                print("Warning: Could not find markers, sending full text.")
                return full_text
            
            extracted_text = full_text[start_index + len(start_marker) : end_index].strip()
            
            anchor = "Next pick due on"
            if anchor in extracted_text:
                try:
                    parts = extracted_text.split(anchor)
                    who_is_on_clock = parts[0].strip()
                    date_string = parts[1].strip().strip('.')
                    
                    # 1. EXTRACT TEAM NAME AND HANDLE
                    team_name_with_prefix = who_is_on_clock.removesuffix(' are on the clock.').strip()
                    
                    if team_name_with_prefix.startswith("The "):
                        prefix = "The "
                        entity_to_tag = team_name_with_prefix[len(prefix):]
                    else:
                        prefix = ""
                        entity_to_tag = team_name_with_prefix

                    owner_handle_match = re.search(r'\((.*?)\)', entity_to_
