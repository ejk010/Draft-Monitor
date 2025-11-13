import requests
import os
from bs4 import BeautifulSoup

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
        # Find the div by its class
        status_div = soup.find("div", {"class": "alert-info"})
        
        if status_div:
            # Get all text from the div, stripping whitespace
            full_text = status_div.get_text(strip=True)
            
            # Define the start and end markers for the text we want
            start_marker = "is currently open."
            end_marker = "Note, auto picks"
            
            # Find the start position
            start_index = full_text.find(start_marker)
            if start_index == -1:
                # Fallback in case text changes, send the whole thing
                print("Warning: Could not find start marker, sending full text.")
                return full_text
            
            # Find the end position
            end_index = full_text.find(end_marker)
            if end_index == -1:
                # Fallback in case text changes, send the whole thing
                print("Warning: Could not find end marker, sending full text.")
                return full_text
            
            # Extract the text between the markers
            # We add len(start_marker) to start *after* the marker
            extracted_text = full_text[start_index + len(start_marker) : end_index]
            
            # Return the cleaned-up text
            return extracted_text.strip()
        else:
            return "Draft status div not found."
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def read_last_status():
    try:
        with open(STATUS_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""

def write_new_status(status):
    with open(STATUS_FILE, 'w') as f:
        f.write(status)

def send_discord_notification(message):
    data = {"content": message}
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=10)
        print("Discord notification sent.")
    except Exception as e:
        print(f"Error sending Discord notification: {e}")

# --- Main script ---
if not WEBHOOK_URL:
    print("Error: DISCORD_WEBHOOK_URL not set.")
    exit()
    
current_status = get_draft_status()
if not current_status:
    print("Could not retrieve current status.")
    exit()

last_status = read_last_status()

if current_status != last_status:
    print("Change detected!")
    # We add a nice header to the clean message
    send_discord_notification(f"**Draft Update:**\n{current_status}")
    write_new_status(current_status)
else:
    print("No change detected.")
