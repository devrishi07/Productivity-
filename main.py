import sqlite3
from datetime import datetime, date, timedelta


def markdone():
    name = input('Enter habit name: ').strip()

    con = sqlite3.connect('habits.db')
    cur = con.cursor()

    # include frequency in the query
    cur.execute("SELECT last_done, streak, frequency, goal_per_frequency, progress FROM habits WHERE name = ?", (name,))
    result = cur.fetchone()

    if not result:
        print(f"Habit '{name}' not found. :(\n")
        con.close()
        return

    last_done, streak, frequency, goal, progress = result
    today = date.today()

    # convert to correct types
    if frequency is not None:
        frequency = int(frequency)
    if goal is not None:
        goal = int(goal)
    if progress is not None:
        progress = int(progress)
    if streak is None:
        streak = 0

    # convert stored date text to date object
    if last_done:
        last_done_date = datetime.strptime(last_done, "%Y-%m-%d").date()
    else:
        last_done_date = None

    # within the same cycle window
    if last_done_date and (today - last_done_date).days < frequency:
        progress += 1
        if progress == goal:
            streak += 1
            last_done_date = today
            print(f"Habit '{name}' goal reached! Streak now {streak}.")
        elif progress > goal:
            progress = goal  # cap progress
            print(f"Habit '{name}' already completed for this cycle.")
        else:
            print(f"Progress updated: {progress}/{goal}")
    else:
        # new cycle or first entry
        streak = 1 if not last_done_date or (today - last_done_date).days > frequency else streak + 1
        last_done_date = today
        progress = 1
        print(f"Habit '{name}' restarted. Current progress: {progress}/{goal}")

    cur.execute(
        "UPDATE habits SET streak = ?, last_done = ?, progress = ? WHERE name = ?",
        (streak, last_done_date.isoformat(), progress, name)
    )

    con.commit()
    con.close()
    print("Update saved.\n")


def add_habit():
    name = input('Enter habit name: ').strip()
    frequency = int(input('Enter frequency in days: '))
    goal = int(input('Enter your goal (times per cycle): '))

    con = sqlite3.connect('habits.db')
    cur = con.cursor()

    cur.execute(
        'INSERT INTO habits (name, frequency, goal_per_frequency, streak, progress) VALUES (?, ?, ?, 0, 0)',
        (name, frequency, goal)
    )

    con.commit()
    con.close()
    print(f"Habit '{name}' added successfully!\n")


def view_habits():
    con = sqlite3.connect('habits.db')
    cur = con.cursor()

    cur.execute("SELECT name, frequency, goal_per_frequency, progress, streak, last_done FROM habits")
    rows = cur.fetchall()
    con.close()

    if not rows:
        print("\nNo habits found.\n")
        return

    print("\nYour Habits:\n")
    for name, freq, goal, progress, streak, last_done in rows:
        last_done_display = last_done if last_done else "Never"
        print(f"• {name}")
        print(f"   Every {freq} day(s)")
        print(f"   Goal: {goal} time(s) per cycle")
        print(f"   Progress: {progress}/{goal}")
        print(f"   Streak: {streak}")
        print(f"   Last done: {last_done_display}\n")


def remove_habit():
    name = input('Enter habit name: ').strip()

    con = sqlite3.connect('habits.db')
    cur = con.cursor()
    cur.execute('DELETE FROM habits WHERE name = ?', (name,))
    con.commit()
    con.close()

    print(f"Habit '{name}' removed successfully!\n")


while True:
    print("1. Add new habit")
    print("2. View habits")
    print("3. Mark done")
    print("4. Remove habit")
    print("5. Exit")

    choice = input("Choose: ")

    if choice == "1":
        add_habit()
    elif choice == "2":
        view_habits()
    elif choice == "3":
        markdone()
    elif choice == "4":
        remove_habit()
    elif choice == "5":
        break
    else:
        print("Invalid choice. Try again.\n")
