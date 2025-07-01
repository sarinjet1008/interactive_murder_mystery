import json
import os

# Location of the game state file
STATE_FILE = "game_state.json"

# ---------------------------
# Load game state
# ---------------------------
def load_game_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    else:
        # If the file doesn't exist, return default state
        return {
            "day": 1,
            "daily_top_suspects": {
                "1": [],
                "2": [],
                "3": []
            },
            "clues_unlocked": {
                "1": [],
                "2": [],
                "3": []
            },
            "interrogation_log": {
                "1": [],
                "2": [],
                "3": []
            }
        }

# ---------------------------
# Save game state
# ---------------------------
def save_game_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)
