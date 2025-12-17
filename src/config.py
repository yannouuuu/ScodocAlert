import os
from dotenv import load_dotenv

load_dotenv()

SCODOC_URL = os.getenv("SCODOC_URL", "https://scodoc.example.com")
CAS_URL = os.getenv("CAS_URL", "https://cas.example.com") # Default, might need adjustment
USERNAME = os.getenv("SCODOC_USER")
PASSWORD = os.getenv("SCODOC_PASSWORD")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BULLETIN_URL = os.getenv("BULLETIN_URL")
VERIFY_SSL = os.getenv("VERIFY_SSL", "True").lower() == "true"
# Semester selection: -1 for latest, -2 for second to last, 0 for first, 1 for second, etc.
SEMESTER_INDEX = int(os.getenv("SEMESTER_INDEX", "-2"))

if not USERNAME or not PASSWORD:
    print("Warning: SCODOC_USER or SCODOC_PASSWORD not set in environment.")
