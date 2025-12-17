import time
import json
import os
import sys
from datetime import datetime
from config import SCODOC_URL, USERNAME, PASSWORD, DISCORD_WEBHOOK_URL, VERIFY_SSL, BULLETIN_URL, SEMESTER_INDEX
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
        
        # Use None as default for evaluations without notes yet
        if note_value is None or note_value == "":
            note_value = None

        # Construct a unique key for this evaluation
        # We use ID, but storing the value allows detecting updates
        stored_value = state.get(eval_id)

        # Case 1: New evaluation we haven't seen
        if eval_id not in state:
            if note_value is not None and note_value != "":
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
            # If there was no note and now there is one
            if stored_value is None and note_value is not None and note_value != "" and note_value != "~":
                print(f"New grade added: {module_title} - {eval_desc} ({note_value})")
                notifier.notify_new_grade(
                    module_name=f"{module_code} - {module_title}",
                    evaluation_name=eval_desc,
                    note=note_value,
                    mean=note_data.get('moy'),
                    min_note=note_data.get('min'),
                    max_note=note_data.get('max'),
                    mention_everyone=True  # Always mention for new grades
                )
            # If it was "~" and now is a real grade, treat as new grade
            elif stored_value == "~" and note_value not in [None, "~", ""]:
                print(f"Grade updated: {module_title} - {eval_desc} ({stored_value} -> {note_value})")
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
            elif stored_value not in [None, "~", ""] and note_value not in [None, "~", ""]:
                print(f"Grade updated: {module_title} - {eval_desc} ({stored_value} -> {note_value})")
                notifier.notify_grade_update(
                    module_name=f"{module_code} - {module_title}",
                    evaluation_name=eval_desc,
                    old_note=stored_value,
                    new_note=note_value
                )
            # If a real grade was removed or set back to pending
            elif stored_value not in [None, "~", ""] and note_value in [None, "~", ""]:
                new_status = "supprimée" if note_value in [None, ""] else "en attente"
                print(f"Grade removed/pending: {module_title} - {eval_desc} ({stored_value} -> {new_status})")
                notifier.notify_grade_update(
                    module_name=f"{module_code} - {module_title}",
                    evaluation_name=eval_desc,
                    old_note=stored_value,
                    new_note=f"Note {new_status}"
                )
            
            state[eval_id] = note_value

import argparse

def main():
    parser = argparse.ArgumentParser(description="ScodocAlert - Grade Monitor")
    parser.add_argument("--loop", action="store_true", help="Run in a continuous loop every 10 minutes")
    args = parser.parse_args()

    print("Starting ScodocAlert...")
    notifier = DiscordNotifier(DISCORD_WEBHOOK_URL, BULLETIN_URL)
    
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
                    # Display all available semesters
                    print(f"Available semesters ({len(semesters)}):")
                    for idx, sem in enumerate(semesters):
                        print(f"  [{idx}] {sem['titre']} (ID: {sem['formsemestre_id']})")
                    
                    # Select semester based on SEMESTER_INDEX
                    try:
                        selected_sem = semesters[SEMESTER_INDEX]
                        sem_id = selected_sem['formsemestre_id']
                        print(f"\n→ Checking semester: {selected_sem['titre']} (ID: {sem_id})")
                    except IndexError:
                        print(f"Error: SEMESTER_INDEX {SEMESTER_INDEX} is out of range (0-{len(semesters)-1})")
                        print("Using last semester as fallback.")
                        selected_sem = semesters[-1]
                        sem_id = selected_sem['formsemestre_id']
                        print(f"→ Checking semester: {selected_sem['titre']} (ID: {sem_id})")
                    
                    grades_data = client.get_grades(sem_id)
                    releve = grades_data.get('relevé', {})
                    
                    # Check if notes are published
                    publie = releve.get('publie', False)
                    message = releve.get('message', '')
                    
                    if not publie:
                        print(f"⚠️  Les notes ne sont pas publiées pour ce semestre.")
                        if message:
                            print(f"   Message: {message}")
                        print(f"   Le fichier d'état restera vide jusqu'à la publication des notes.")
                    
                    # Process Ressources (R1.01, etc.)
                    ressources = releve.get('ressources', {})
                    for code, res in ressources.items():
                        process_evaluations(res, code, res['titre'], state, notifier, is_initialization)
                        
                    # Process SAEs
                    saes = releve.get('saes', {})
                    for code, sae in saes.items():
                        process_evaluations(sae, code, sae['titre'], state, notifier, is_initialization)
                        
                    save_state(state)
                    if len(state) > 0:
                        print(f"✓ Check complete. {len(state)} evaluations tracked in state file.")
                    else:
                        print("✓ Check complete. No evaluations to track yet.")

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
