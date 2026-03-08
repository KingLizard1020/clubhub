import sqlite3

def seed_database():
    conn = sqlite3.connect('club_hub.db')
    cursor = conn.cursor()

    # 1. Mock Data for Members (Notice the CS and EE majors)
    members_data = [
        ('Alice', 'Chen', 'achen@school.edu', 'Computer Science', 'Active'),
        ('Marcus', 'Johnson', 'mjohnson@school.edu', 'Electrical Engineering', 'Active'),
        ('Elena', 'Rodriguez', 'erodriguez@school.edu', 'Computer Science', 'Interested')
    ]

    # 2. Mock Data for Events
    events_data = [
        ('Intro to VLSI Design', '2026-03-10', 'Workshop'),
        ('Embedded Systems Hackathon', '2026-03-15', 'Project Meeting'),
        ('AI in Space Exploration', '2026-03-20', 'Seminar')
    ]

    # 3. Insert Members using Parameterized Queries (?)
    cursor.executemany('''
        INSERT INTO members (first_name, last_name, email, major, status)
        VALUES (?, ?, ?, ?, ?)
    ''', members_data)

    # 4. Insert Events
    cursor.executemany('''
        INSERT INTO events (title, event_date, event_type)
        VALUES (?, ?, ?)
    ''', events_data)

    # 5. Mock Data for Attendance (Linking member_id to event_id)
    # Alice (1) and Marcus (2) attended the VLSI workshop (1)
    # Alice (1) and Elena (3) attended the AI seminar (3)
    attendance_data = [
        (1, 1), 
        (2, 1),
        (1, 3),
        (3, 3)
    ]

    cursor.executemany('''
        INSERT INTO attendance (member_id, event_id)
        VALUES (?, ?)
    ''', attendance_data)

    # Save and close
    conn.commit()
    conn.close()

    print("Success: Mock data injected into the database!")

if __name__ == "__main__":
    seed_database()