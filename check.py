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
TEAM_NAME_MAP = {
    "Diamondbacks": "<@&773898276940152833>",
    "Braves": "<@&622615242978885632>",
    "Orioles": "<@&728717530096468149>",
    "Red Sox": "<@&1180931211858809023>",
    "Cubs": "<@&773897833211625473>",
    "White Sox": "<@&622615457299693578>",
    "Reds": "<@&773898419143442432>",
    "Indians": "<@&773898193041358879>",
    "Rockies": "<@&773898540321079316>",
    "Tigers": "<@&622615931625144341>",
    "Astros": "<@&962525228636987402>",
    "Royals": "<@&622614419486015510>",
    "Angels": "<@&622613488824483840>",
    "Dodgers": "<@&962525782977150996>",
    "Marlins": "<@&752626736125968474>",
    "Brewers": "<@&622613398701604865>",
    "Twins": "<@&728718027645780018>",
    "Mets": "<@&622613734896041994>",
    "Yankees": "<@&622952290428387329>",
    "Athletics": "<@&773897507272261683>",
    "Phillies": "<@&622614284979011595>",
    "Pirates": "<@&622615936234684416>",
    "Cardinals": "<@&622613261841596426>",
    "Padres": "<@&622618093868548097>",
    "Giants": "<@&622615034157203469>",
    "Mariners": "<@&622612991413714975>",
    "Rays": "<@&623340295517634560>",
    "Rangers": "<@&622613054642978817>",
    "Blue Jays": "<@&622615298322989070>",
    "Nationals": "<@&1180930959642722404>",
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
            
            start_index = full_text.find(start_marker)
            
            if start_index == -1:
                print("Warning: Could not find start marker, sending full text.")
                return full_text
            
            extracted_text = full_text[start_index + len(start_marker) :].strip()
            
            anchor = "Next pick due on"
            if anchor in extracted_text:
                try:
                    parts = extracted_text.split(anchor)
                    who_is_on_clock = parts[0].strip()
                    # date_string_raw is now " 11/15/2025 at 3:16 AM PST.Note, auto picks..."
                    date_string_raw = parts[1].strip() 

                    # --- NEW FIX: Isolate the date string ---
                    date_part = ""
                    if "PST" in date_string_raw:
                        end_index = date_string_raw.find("PST") + 3
                        date_part = date_string_raw[:end_index].strip().strip('.')
                    elif "PDT" in date_string_raw:
                        end_index = date_string_raw.find("PDT") + 3
                        date_part = date_string_raw[:end_index].strip().strip('.')
                    else:
                        # Fallback if no timezone is found
                        date_part = date_string_raw.strip().strip('.')
                    # --- END NEW FIX ---

                    # --- NEW LOGIC FOR TAGGING ---
                    team_owner_string = who_is_on_clock.removesuffix(' are on the clock.').strip()
                    
                    prefix = ""
                    if team_owner_string.startswith("The "):
                        prefix = "The "
                    
                    owner_handle_match = re.search(r'\((.*?)\)', team_owner_string)
                    owner_handle_display = ""
                    if owner_handle_match:
                        owner_handle_display = owner_handle_match.group(0)

                    team_name = team_owner_string.removeprefix(prefix).removesuffix(owner_handle_display).strip()

                    mention = TEAM_NAME_MAP.get(team_name, f"@{team_name}")
                    # --- END NEW LOGIC ---
                    
                    # --- ROBUST TIMEZONE FIX START ---
                    # We now use the clean 'date_part'
                    date_part = date_part.removesuffix('PST').removesuffix('PDT').strip()
                    pacific_tz = gettz("America/Los_Angeles")
                    naive_dt = parse(date_part)
                    aware_dt = naive_dt.replace(tzinfo=pacific_tz)
                    unix_timestamp = int(aware_dt.timestamp())
                    # --- ROBUST TIMEZONE FIX END ---
                    
                    # --- MODIFIED FINAL MESSAGE ---
                    final_message = (
                        f"{prefix}{mention} {owner_handle_display} are on the clock!\n"
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
