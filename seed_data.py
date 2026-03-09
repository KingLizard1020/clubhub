from db import get_connection
from db_setup import setup_database


def seed_database():
    """Reset local demo data so the app starts with a predictable dataset."""
    setup_database()

    prospects_data = [
        ("Jordan", "Lee", "jlee@school.edu", "555-0101", "Computer Science", "2027", "Interest Fair", "Interested in joining the robotics team."),
        ("Priya", "Patel", "ppatel@school.edu", "555-0102", "Business", "2028", "Instagram", "Wants to help with event planning."),
    ]

    members_data = [
        ("Alice", "Chen", "achen@school.edu", "555-0110", "Computer Science", "2026", "active", "Secretary and regular volunteer."),
        ("Marcus", "Johnson", "mjohnson@school.edu", "555-0111", "Electrical Engineering", "2027", "officer", "Leads workshop logistics."),
        ("Elena", "Rodriguez", "erodriguez@school.edu", "555-0112", "Mechanical Engineering", "2026", "active", "Often helps with check-in."),
    ]

    events_data = [
        ("Spring Welcome Meeting", "Kick off the semester and share plans.", "2026-03-10", "18:00", "19:00", "Student Center 201", "meeting", 1),
        ("Community Service Day", "Volunteer event with a local nonprofit.", "2026-03-15", "09:00", "12:00", "City Park", "service", 0),
        ("Resume Workshop", "Peer review and resume building session.", "2026-03-20", "17:30", "18:30", "Career Lab", "workshop", 0),
    ]

    rsvp_data = [
        ("achen@school.edu", "Spring Welcome Meeting", "yes"),
        ("mjohnson@school.edu", "Spring Welcome Meeting", "yes"),
        ("erodriguez@school.edu", "Spring Welcome Meeting", "maybe"),
        ("achen@school.edu", "Community Service Day", "yes"),
    ]

    attendance_data = [
        ("achen@school.edu", "Spring Welcome Meeting", "present", "self"),
        ("mjohnson@school.edu", "Spring Welcome Meeting", "present", "admin"),
        ("achen@school.edu", "Resume Workshop", "late", "self"),
    ]

    with get_connection() as conn:
        cursor = conn.cursor()

        # Clear child tables first so foreign key constraints are not violated.
        cursor.execute("DELETE FROM attendance")
        cursor.execute("DELETE FROM rsvps")
        cursor.execute("DELETE FROM prospects")
        cursor.execute("DELETE FROM events")
        cursor.execute("DELETE FROM members")

        cursor.executemany(
            """
            INSERT INTO prospects (first_name, last_name, email, phone, major, class_year, interest_source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            prospects_data,
        )

        cursor.executemany(
            """
            INSERT INTO members (first_name, last_name, email, phone, major, class_year, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            members_data,
        )

        cursor.executemany(
            """
            INSERT INTO events (title, description, event_date, start_time, end_time, location, category, is_required)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            events_data,
        )

        # Seed RSVP and attendance data by email/title so the sample data stays easy to read without hard-coding database ids.
        member_lookup = {
            row["email"]: row["member_id"]
            for row in cursor.execute("SELECT member_id, email FROM members")
        }
        event_lookup = {
            row["title"]: row["event_id"]
            for row in cursor.execute("SELECT event_id, title FROM events")
        }

        cursor.executemany(
            """
            INSERT INTO rsvps (member_id, event_id, status)
            VALUES (?, ?, ?)
            """,
            [
                (member_lookup[email], event_lookup[title], status)
                for email, title, status in rsvp_data
            ],
        )

        cursor.executemany(
            """
            INSERT INTO attendance (member_id, event_id, attendance_status, check_in_method)
            VALUES (?, ?, ?, ?)
            """,
            [
                (member_lookup[email], event_lookup[title], status, method)
                for email, title, status, method in attendance_data
            ],
        )

        conn.commit()

    print("Success: Mock data injected into the database!")

if __name__ == "__main__":
    seed_database()