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
# Format for Role ID: <@&ROLE_ID>
# Format for User ID: <@USER_ID>
DISCORD_ID_MAP = {
    # Replace the example IDs with the actual IDs from your server
    "bigdaddybrett05": "<@&123456789012345678>", # Example Role ID for Giants owner
    "White Sox": "<@&1438619550559240314>",    # Example User ID for another owner
    "ownerhandle3": "@Draft",                     # Example of a hardcoded text tag for testing
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
                    
                    # 1. EXTRACT OWNER HANDLE AND TEAM NAME
                    team_name_with_prefix = who_is_on_clock.removesuffix(' are on the clock.').strip()
                    
                    # Use regex to find the owner handle inside parentheses (e.g., bigdaddybrett05)
                    owner_handle_match = re.search(r'\((.*?)\)', team_name_with_prefix)

                    if team_name_with_prefix.startswith("The "):
                        prefix = "The "
                        entity_to_tag = team_name_with_prefix[len(prefix):]
                    else:
                        prefix = ""
                        entity_to_tag = team_name_with_prefix
                    
                    # 2. PERFORM ID LOOKUP
                    mention = f"@{entity_to_tag}" # Default to name if handle not found
                    
                    if owner_handle_match:
                        owner_handle = owner_handle_match.group(1)
                        # Look up the ID in the dictionary
                        mention = DISCORD_ID_MAP.get(owner_handle, f"@{entity_to_tag}")
                    
                    # 3. ROBUST TIMEZONE PARSING
                    date_part = date_string.removesuffix('PST').removesuffix('PDT').strip()
                    pacific_tz = gettz("America/Los_Angeles")
                    naive_dt = parse(date_part)
                    aware_dt = naive_dt.replace(tzinfo=pacific_tz)
                    unix_timestamp = int(aware_dt.timestamp())
                    
                    # 4. BUILD THE FINAL MESSAGE WITH TAGGING
                    final_message = (
                        # Note: mention is now an ID (e.g., <@&ID>) or plain text (@Name)
                        f"{prefix}{mention} is on the clock!\n"
                        f"Next pick due: <t:{unix_timestamp}:f>"
                    )
                    return final_message

                except Exception as e:
                    print(f"Error parsing date: {e}. Defaulting to plain text.")
                    return extracted_text
            
            return extracted_text
            # --- End of logic ---
        else:
            return "Draft status div not found."
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

# --- Rest of the file is unchanged ---

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
    send_discord_notification(f"**Draft Update:**\n{current_status}")
    write_new_status(current_status)
else:
    print("No change detected.")
