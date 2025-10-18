import random
import os
import json
import shutil
import csv
from datetime import datetime

# -----------------------
# CONFIGURATION
# -----------------------
K = 4  # Elo K-factor
SAVE_FILE = "manga_scores.json"
BACKUP_DIR = "backups"
UNDO_STACK = []

# Example manga data: title -> original score
manga_dict = {
    "EXAMPLE1": {"score": 100, "comparisons": 0},
    "EXAMPLE2": {"score": 50, "comparisons": 0},
    "EXAMPLE3": {"score": 70, "comparisons": 0}
}

# Track battle count
battle_count = 0

# -----------------------
# SAVE / LOAD FUNCTIONS
# -----------------------
def backup_file():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"manga_scores_{timestamp}.json")
    if os.path.exists(SAVE_FILE):
        shutil.copy(SAVE_FILE, backup_path)

def save_scores():
    global battle_count
    backup_file()
    with open(SAVE_FILE, "w") as f:
        json.dump({"scores": manga_dict, "battle_count": battle_count}, f, indent=4)
    print(f"Scores saved to {SAVE_FILE}.")
    export_to_csv()

def load_scores():
    global battle_count, manga_dict
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            loaded_scores = data.get("scores", {})
            for key in loaded_scores:
                if isinstance(loaded_scores[key], dict):
                    manga_dict[key] = loaded_scores[key]
                else:
                    # backward compatibility with old format
                    manga_dict[key] = {"score": loaded_scores[key], "comparisons": 0}
            battle_count = data.get("battle_count", 0)
        print(f"Scores loaded from {SAVE_FILE}.")
    else:
        print("No save file found. Starting fresh.")

# -----------------------
# ELO SCORING FUNCTION
# -----------------------
def update_scores(score_A, score_B, winner):
    expected_A = 1 / (1 + 10 ** ((score_B - score_A) / 400))
    actual_A = 1 if winner == 'A' else 0
    score_A_new = score_A + K * (actual_A - expected_A)

    expected_B = 1 / (1 + 10 ** ((score_A - score_B) / 400))
    actual_B = 1 if winner == 'B' else 0
    score_B_new = score_B + K * (actual_B - expected_B)

    return score_A_new, score_B_new

# -----------------------
# EXPORT TO CSV (Excel-readable)
# -----------------------
def export_to_csv():
    sorted_manga = sorted(manga_dict.items(), key=lambda x: x[1]["score"], reverse=True)
    with open("manga_scores.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Manga", "Score", "Comparisons"])
        for manga, stats in sorted_manga:
            writer.writerow([manga, f"{stats['score']:.1f}", stats["comparisons"]])
    print("Exported scores to manga_scores.csv")

# -----------------------
# UNDO FUNCTION
# -----------------------
def undo_last_battle():
    global UNDO_STACK, manga_dict, battle_count
    if UNDO_STACK:
        manga_dict, battle_count = UNDO_STACK.pop()
        print("Last battle undone.")
    else:
        print("No battle to undo.")

# -----------------------
# BATTLE SIMULATION
# -----------------------
def battle(manga1, manga2):
    global battle_count, UNDO_STACK
    print(f"\nBattle #{battle_count + 1}")
    print(f"1: {manga1} (Score: {manga_dict[manga1]['score']:.1f}, Compared: {manga_dict[manga1]['comparisons']} times)")
    print(f"2: {manga2} (Score: {manga_dict[manga2]['score']:.1f}, Compared: {manga_dict[manga2]['comparisons']} times)")
    choice = input("Which manga wins? (1/2 or u=undo, s=save, q=quit): ").strip().lower()

    if choice == "1":
        winner = 'A'
    elif choice == "2":
        winner = 'B'
    elif choice == "s":
        save_scores()
        return True
    elif choice == "q":
        save_scores()
        print("Exiting...")
        exit()
    elif choice == "u":
        undo_last_battle()
        return False
    else:
        print("Invalid choice. Try again.")
        return False

    # Save current state for undo
    UNDO_STACK.append((json.loads(json.dumps(manga_dict)), battle_count))  # deep copy

    score_A, score_B = update_scores(manga_dict[manga1]["score"], manga_dict[manga2]["score"], winner)
    manga_dict[manga1]["score"] = score_A
    manga_dict[manga2]["score"] = score_B

    # Track comparisons
    manga_dict[manga1]["comparisons"] += 1
    manga_dict[manga2]["comparisons"] += 1

    battle_count += 1
    print(f"Updated Scores -> {manga1}: {score_A:.1f}, {manga2}: {score_B:.1f}")
    return True

# -----------------------
# MAIN LOOP
# -----------------------
def main():
    load_scores()
    while True:
        manga1, manga2 = random.sample(list(manga_dict.keys()), 2)
        battle_done = battle(manga1, manga2)
        if not battle_done:
            continue

if __name__ == "__main__":
    main()
