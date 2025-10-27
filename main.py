import sqlite3
from datetime import datetime, date, timedelta


#helper fucntions
def _init_table():
    con = sqlite3.connect('habits.db')
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        frequency INTEGER NOT NULL,
        goal_per_frequency INTEGER NOT NULL,
        streak INTEGER NOT NULL DEFAULT 0,
        progress INTEGER NOT NULL DEFAULT 0,
        last_done TEXT
    )
    """)
    con.commit()
    con.close()

_init_table()  # ensure table exists

def read_int(prompt):
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            return int(s)
        print("Please enter a positive number.")

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
    
    if last_done:
        try:
            last_done_date = datetime.strptime(last_done, "%Y-%m-%d").date()
        except ValueError:
            # malformed stored value; treat as never done
            last_done_date = None
        else:
            last_done_date = None


    days_since = (today - last_done_date).days if last_done_date else None
    same_cycle = (last_done_date is not None) and (days_since < frequency)

    if same_cycle:
        #stay in same cycle
        if progress < goal:
            progress += 1
            if progress == goal:
                streak += 1
            else:
                print(f"Progress updated: {progress}/{goal}")

    else:
        #start a new cycle
        if last_done_date is not None and progress >= goal:
            streak += 1
        else:
            streak = 0

        progress = 1
        last_done_date = today

    cur.execute(
        "UPDATE habits SET streak = ?, last_done = ?, progress = ? WHERE name = ?",
        (streak, last_done_date.isoformat(), progress, name),
    )

    con.commit()
    con.close()
    print("Update saved.\n")


def add_habit():
    name = input('Enter habit name: ').strip()
    frequency = read_int('Enter frequency in days: ')
    goal = read_int('Enter your goal (times per cycle): ')


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

        remaining = max(0, int(goal) - int(progress))
        print(f"   Progress: {progress}/{goal}. Remaining: {remaining}")




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
