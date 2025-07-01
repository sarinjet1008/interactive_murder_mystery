import json
import os

def load_clue(day: int, suspect: str):
    # Try both day 1 and day1 format
    for day_format in [f"day {day}", f"day{day}"]:
        # Try both JSON and TXT formats
        for ext in [".json", ".txt"]:
            filepath = f"../data/clues/{day_format}/{suspect.lower()}{ext}"
            if os.path.exists(filepath):
                if ext == ".json":
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return f"🧩 Clue about {suspect.capitalize()}: {data.get('clue', 'No clue found')}"
                else:  # .txt file
                    with open(filepath, "r", encoding="utf-8") as f:
                        clue = f.read().strip()
                        return f"🧩 Clue about {suspect.capitalize()}: {clue}"
    return f"No new clues for {suspect.capitalize()} today."
