import requests
import os
from bs4 import BeautifulSoup
from dateutil.parser import parse  # We are adding this new library
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
            
            # --- Start of new logic ---
            start_marker = "is currently open."
            end_marker = "Note, auto picks"
            
            start_index = full_text.find(start_marker)
            end_index = full_text.find(end_marker)
            
            if start_index == -1 or end_index == -1:
                print("Warning: Could not find markers, sending full text.")
                return full_text
            
            extracted_text = full_text[start_index + len(start_marker) : end_index].strip()
            
            # Now, we parse the date from the extracted text
            anchor = "Next pick due on"
            if anchor in extracted_text:
                try:
                    # Split the string into "who is on the clock" and "the date string"
                    parts = extracted_text.split(anchor)
                    who_is_on_clock = parts[0].strip()
                    date_string = parts[1].strip().strip('.') # Get "11/13/2025 at 8:56 PM PST"
                    
                    # Use dateutil.parser to "understand" the date string
                    # This is the magic part that handles "PST"
                    due_datetime = parse(date_string)
                    
                    # Convert the datetime object to a Unix timestamp (an integer)
                    unix_timestamp = int(due_datetime.timestamp())
                    
                    # Build the new message with Discord's timestamp format
                    # <t:TIMESTAMP:f> = Full Date (e.g., November 13, 2025 at 10:56 PM)
                    # <t:TIMESTAMP:R> = Relative Time (e.g., in 2 hours)
                    final_message = (
                        f"{who_is_on_clock}\n"
                        f"Next pick due: <t:{unix_timestamp}:f> (which is <t:{unix_timestamp}:R>)"
                    )
                    return final_message

                except Exception as e:
                    print(f"Error parsing date: {e}. Defaulting to plain text.")
                    return extracted_text
