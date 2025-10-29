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
    name = input('Enter habit name: ').strip().lower()

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
                print(f"Habit {name} goal reached for this cycle!")
            else:
                print(f"Progress updated: {progress}/{goal}")
        else:
            print(f"Habit {name} already completed this cycle")
        
        last_done_date = today
    
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
        (streak, last_done_date.isoformat(), progress, name)
    )

    con.commit()
    con.close()
    print("Update saved.\n")


def add_habit():
    name = input('Enter habit name: ').strip().lower()
    frequency = read_int('Enter frequency in days: ')
    goal = read_int('Enter your goal (times per cycle): ')

    if frequency < 1 or goal < 1:
        print("Frequency and goal must be >= 1.")
        return 


    con = sqlite3.connect('habits.db')
    cur = con.cursor()

    try:
        cur.execute(
            'INSERT INTO habits (name, frequency, goal_per_frequency, streak, progress) VALUES (?, ?, ?, 0, 0)',
            (name, frequency, goal)
        )
        con.commit()
        print(f"Habit '{name}' added successfully!\n")

    except sqlite3.IntegrityError:
        print(f"A habit with the name {name} already exists.")

    con.close()



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
        print(f"   Streak: {streak}")
        print(f"   Last done: {last_done_display}\n")

        remaining = max(0, int(goal) - int(progress))
        print(f"   Progress: {progress}/{goal}. Remaining: {remaining}")
        print()



def remove_habit():
    name = input('Enter habit name: ').strip().lower()

    con = sqlite3.connect('habits.db')
    cur = con.cursor()
    cur.execute('DELETE FROM habits WHERE name = ?', (name,))
    con.commit()
    con.close()

    print(f"Habit '{name}' removed successfully!\n")

def edit_habit():
    lookup = input("Enter habit name: ").strip().lower()
    name = lookup.lower().strip()  # keep consistent with your add/mark normalization

    con = sqlite3.connect("habits.db")
    cur = con.cursor()

    row = cur.execute(
        "SELECT id, name, frequency, goal_per_frequency, streak, progress, last_done FROM habits WHERE name = ?",
        (name,)
    ).fetchone()

    if not row:
        print(f"Habit '{lookup}' not found.\n")
        con.close()
        return

    habit_id, cur_name, cur_freq, cur_goal, cur_streak, cur_prog, cur_last = row

    while True:
        print("\nCurrent values:")
        print(f"  name: {cur_name}")
        print(f"  frequency (days): {cur_freq}")
        print(f"  goal (per cycle): {cur_goal}")
        print(f"  streak: {cur_streak}")
        print(f"  progress: {cur_prog}")
        print(f"  last_done: {cur_last or 'Never'}")
        print("\nEdit:")
        print("1. name")
        print("2. frequency")
        print("3. goal")
        print("4. save and exit")
        print("5. discard and exit")

        choice = read_int("Choose: ")

        if choice == 1:
            new_name_input = input("Enter new name: ").strip()
            new_name = new_name_input.lower().strip()

            if not new_name:
                print("Name cannot be empty.")
                continue
            # optional: uniqueness check
            exists = cur.execute("SELECT 1 FROM habits WHERE name = ? AND id <> ?", (new_name, habit_id)).fetchone()
            if exists:
                print("That name already exists. Choose another.")
                continue
            cur_name = new_name

            

        elif choice == 2:
            new_freq = read_int("Enter new frequency (days >= 1): ")
            if new_freq < 1:
                print("Frequency must be >= 1.")
                continue
            cur_freq = new_freq
            # optional rule: when frequency changes, reset progress to 0 to avoid mismatch
            cur_prog = 0

        elif choice == 3:
            new_goal = read_int("Enter new goal (>= 1): ")
            if new_goal < 1:
                print("Goal must be >= 1.")
                continue
            cur_goal = new_goal
            # optional: clamp current progress to new goal
            if cur_prog > cur_goal:
                cur_prog = cur_goal

        elif choice == 4:
            # Save all edits atomically
            cur.execute(
                """UPDATE habits
                   SET name = ?, frequency = ?, goal_per_frequency = ?, progress = ?
                   WHERE id = ?""",
                (cur_name, cur_freq, cur_goal, cur_prog, habit_id)
            )
            con.commit()
            print("Saved.\n")
            break

        elif choice == 5:
            print("No changes saved.\n")
            break

        else:
            print("Invalid choice. Select 1-5.")

    con.close()
      
    

while True:
    print("1. Add new habit")
    print("2. View habits")
    print("3. Mark done")
    print("4. Edit habit")
    print("5. Remove habit")
    print("6. Exit")

    choice = input("Choose: ")

    if choice == "1":
        add_habit()
    elif choice == "2":
        view_habits()
    elif choice == "3":
        markdone()
    elif choice == "4":
        edit_habit()
    elif choice == "5":
        remove_habit()
    elif choice == "6":
        break
    else:
        print("Invalid choice. Try again.\n")
