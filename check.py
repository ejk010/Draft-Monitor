import requests
import os
from bs4 import BeautifulSoup
from dateutil.parser import parse
import datetime

# --- Configuration ---
LEAGUE_URL = "https://www.pennantchase.com/league/baseball/home?lgid=691"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
STATUS_FILE = "last_status.txt"
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
