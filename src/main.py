import time
import json
import os
import sys
from datetime import datetime
from config import SCODOC_URL, USERNAME, PASSWORD, DISCORD_WEBHOOK_URL, VERIFY_SSL
from gateway_client import GatewayClient
from discord_notifier import DiscordNotifier
import urllib3

# Suppress SSL warnings
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

STATE_FILE = "scodoc_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def process_evaluations(resource_dict, module_code, module_title, state, notifier, is_initialization=False):
    """
    Iterates through evaluations in a resource (UE/SAE) and checks for changes.
    is_initialization: True if this is the first run (state file is empty/new)
    """
    evaluations = resource_dict.get('evaluations', [])
    for eval_item in evaluations:
        eval_id = str(eval_item['id'])
        eval_desc = eval_item['description']
        
        note_data = eval_item.get('note', {})
        note_value = note_data.get('value')
        
        # Skip if no note value (or empty)
        if not note_value:
            continue

        # Construct a unique key for this evaluation
        # We use ID, but storing the value allows detecting updates
        stored_value = state.get(eval_id)

        # Case 1: New evaluation we haven't seen
        if eval_id not in state:
            print(f"New evaluation found: {module_title} - {eval_desc} ({note_value})")
            # Only notify if it's not a placeholder "~" (unless you want to notify for placeholders too)
            if note_value != "~":
                notifier.notify_new_grade(
                    module_name=f"{module_code} - {module_title}",
                    evaluation_name=eval_desc,
                    note=note_value,
                    mean=note_data.get('moy'),
                    min_note=note_data.get('min'),
                    max_note=note_data.get('max'),
                    mention_everyone=not is_initialization  # Don't mention during init
                )
            state[eval_id] = note_value
        
        # Case 2: Existing evaluation, value changed
        elif stored_value != note_value:
            print(f"Grade updated: {module_title} - {eval_desc} ({stored_value} -> {note_value})")
            
            # If it was "~" and now is a real grade, treat as new grade
            if stored_value == "~" and note_value != "~":
                 notifier.notify_new_grade(
                    module_name=f"{module_code} - {module_title}",
                    evaluation_name=eval_desc,
                    note=note_value,
                    mean=note_data.get('moy'),
                    min_note=note_data.get('min'),
                    max_note=note_data.get('max'),
                    mention_everyone=True  # Always mention for updates
                )
            # If it changed from one real grade to another
            elif stored_value != "~" and note_value != "~":
                notifier.notify_grade_update(
                    module_name=f"{module_code} - {module_title}",
                    evaluation_name=eval_desc,
                    old_note=stored_value,
                    new_note=note_value
                )
            
            state[eval_id] = note_value

import argparse

def main():
    parser = argparse.ArgumentParser(description="ScodocAlert - Grade Monitor")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop every 10 minutes")
    args = parser.parse_args()

    print("Starting ScodocAlert...")
    notifier = DiscordNotifier(DISCORD_WEBHOOK_URL)
    
    client = GatewayClient(SCODOC_URL, USERNAME, PASSWORD, verify_ssl=VERIFY_SSL)
    
    while True:
        try:
            state = load_state()
            is_initialization = len(state) == 0  # First run if state is empty
            
            # Re-login every time to ensure fresh session (or handle expiration)
            # Ideally we check if session is valid, but re-login is safer for long running
            if not client.login():
                print("Login failed. Retrying in 5 minutes.")
            else:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching data...")
                init_data = client.get_initial_data()
                semesters = init_data.get('semestres', [])
                
                if not semesters:
                    print("No semesters found.")
                else:
                    # Check the latest semester
                    latest_sem = semesters[-1]
                    sem_id = latest_sem['formsemestre_id']
                    print(f"Checking semester: {latest_sem['titre']} ({sem_id})")
                    
                    grades_data = client.get_grades(sem_id)
                    releve = grades_data.get('relevé', {})
                    
                    # Process Ressources (R1.01, etc.)
                    ressources = releve.get('ressources', {})
                    for code, res in ressources.items():
                        process_evaluations(res, code, res['titre'], state, notifier, is_initialization)
                        
                    # Process SAEs
                    saes = releve.get('saes', {})
                    for code, sae in saes.items():
                        process_evaluations(sae, code, sae['titre'], state, notifier, is_initialization)
                        
                    save_state(state)
                    print("Check complete. State saved.")

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
        
        if not args.loop:
            break
            
        print("Waiting 5 minutes...")
        time.sleep(300) # 5 minutes

if __name__ == "__main__":
    main()
