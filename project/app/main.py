import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from interrogate import ask_question
from clue_engine import load_clue

suspects = ["zane", "serena", "logan", "jasmine", "nora", "troy", "evelyn"]

def main():
    print("🎯 Welcome to Yacht Murder: Detective Mode")
    day = 1
    while day <= 3:
        print(f"\n🌅 Day {day} begins. You may interrogate any suspect.")

        interviewed = set()
        while len(interviewed) < len(suspects):
            while True:
                print("\nAvailable suspects:")
                for suspect in suspects:
                    if suspect not in interviewed:
                        print(f"- {suspect.capitalize()}")
                chosen = input("Who would you like to interrogate? (type 'done' to skip, 'exit' to quit): ").lower().strip()
                if chosen == 'done':
                    break
                if chosen == 'exit':
                    print("\nThank you for playing! Goodbye!")
                    return
                if chosen not in suspects or chosen in interviewed:
                    print("Invalid suspect name. Please try again.")
                    continue

                print(f"\nInterrogating {chosen.capitalize()}. Type 'exit' to stop anytime.")
                for i in range(5):
                    q = input(f"❓ Q{i+1}: ").strip()
                    if q.lower() == 'exit':
                        break
                    print("💬", ask_question(chosen, q))
                interviewed.add(chosen)
                break

        print("\nAt the end of Day", day)
        top_suspects = input("Enter your top 3 suspects (comma-separated): ").split(",")
        top_suspects = [s.strip().lower() for s in top_suspects]

        print("\n📦 New Clues Unlocked:")
        for s in top_suspects:
            print(load_clue(day, s))

        day += 1

    print("\n🕵️ Final Accusation Time!")
    guess = input("Who do you accuse of the murder? ").strip().lower()
    print(f"🎬 You accused: {guess.capitalize()}")
    print("✅ Thanks for playing!")

if __name__ == "__main__":
    main()
