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
                    
                    # 1. EXTRACT TEAM NAME FOR TAGGING
                    # who_is_on_clock is "The Giants (bigdaddybrett05) are on the clock."
                    # We remove the suffix to isolate the taggable entity.
                    team_name = who_is_on_clock.removesuffix(' are on the clock.').strip()
                    
                    # 2. DYNAMIC TIMEZONE FIX
                    date_part = date_string.removesuffix('PST').removesuffix('PDT').strip()
                    pacific_tz = gettz("America/Los_Angeles")
                    naive_dt = parse(date_part)
                    aware_dt = naive_dt.replace(tzinfo=pacific_tz)
                    unix_timestamp = int(aware_dt.timestamp())
                    
                    # 3. BUILD THE FINAL MESSAGE WITH TAGGING
                    final_message = (
                        # Note: The mention only works if a role/user has the exact name.
                        f"**@{team_name} is on the clock!**\n"
                        f"Next pick due: <t:{unix_timestamp}:f>"
                    )
                    return final_message

                except Exception as e:
                    print(f"Error parsing date: {e}. Defaulting
