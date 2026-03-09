import sqlite3

import pandas as pd

from db import fetch_all, fetch_one, get_connection


# These lists keep the allowed options in one place so both Streamlit apps use the same vocabulary.
MEMBER_STATUSES = ["active", "inactive", "officer", "alumni"]
EVENT_CATEGORIES = ["meeting", "social", "service", "recruitment", "workshop", "other"]
RSVP_STATUSES = ["yes", "no", "maybe"]
ATTENDANCE_STATUSES = ["present", "late", "excused", "absent"]


def _as_dataframe(rows, columns):
    """Convert query results into a DataFrame so Streamlit can render tables directly."""
    return pd.DataFrame(rows, columns=columns)


def get_dashboard_summary():
    """Return the small set of counts shown at the top of the admin dashboard."""
    open_prospects = fetch_one(
        "SELECT COUNT(*) AS total FROM prospects WHERE status != 'converted'"
    )["total"]
    active_members = fetch_one(
        "SELECT COUNT(*) AS total FROM members WHERE status = 'active'"
    )["total"]
    upcoming_events = fetch_one(
        "SELECT COUNT(*) AS total FROM events WHERE date(event_date) >= date('now')"
    )["total"]
    total_check_ins = fetch_one("SELECT COUNT(*) AS total FROM attendance")["total"]

    return {
        "open_prospects": open_prospects,
        "active_members": active_members,
        "upcoming_events": upcoming_events,
        "total_check_ins": total_check_ins,
    }


def get_pending_prospects_df():
    """Return prospects that still need admin review or conversion."""
    rows = fetch_all(
        """
        SELECT
            prospect_id,
            first_name || ' ' || last_name AS name,
            email,
            major,
            class_year,
            interest_source,
            created_at
        FROM prospects
        WHERE status != 'converted'
        ORDER BY created_at DESC
        """
    )
    columns = ["prospect_id", "name", "email", "major", "class_year", "interest_source", "created_at"]
    return _as_dataframe(rows, columns)


def get_members_df():
    """Return a member list shaped for the admin table."""
    rows = fetch_all(
        """
        SELECT
            member_id,
            first_name || ' ' || last_name AS name,
            email,
            major,
            class_year,
            status,
            joined_at
        FROM members
        ORDER BY created_at DESC
        """
    )
    columns = ["member_id", "name", "email", "major", "class_year", "status", "joined_at"]
    return _as_dataframe(rows, columns)


def get_upcoming_events_df():
    """Return upcoming events for admin-facing tables."""
    rows = fetch_all(
        """
        SELECT
            event_id,
            title,
            event_date,
            COALESCE(start_time, '') AS start_time,
            COALESCE(location, '') AS location,
            category,
            is_required
        FROM events
        WHERE date(event_date) >= date('now')
        ORDER BY event_date ASC, start_time ASC
        """
    )
    columns = ["event_id", "title", "event_date", "start_time", "location", "category", "is_required"]
    return _as_dataframe(rows, columns)


def get_upcoming_events():
    """Return lightweight event records for member-facing dropdowns and previews."""
    return fetch_all(
        """
        SELECT
            event_id,
            title,
            event_date,
            COALESCE(start_time, '') AS start_time,
            COALESCE(location, '') AS location
        FROM events
        WHERE date(event_date) >= date('now')
        ORDER BY event_date ASC, start_time ASC
        """
    )


def get_event_summary_df():
    """Return one row per event with RSVP totals and attendance totals side by side."""
    rows = fetch_all(
        """
        SELECT
            events.event_id,
            events.title,
            events.event_date,
            events.category,
            COALESCE(rsvp_counts.yes_count, 0) AS rsvp_yes,
            COALESCE(rsvp_counts.maybe_count, 0) AS rsvp_maybe,
            COALESCE(rsvp_counts.no_count, 0) AS rsvp_no,
            COALESCE(attendance_counts.present_count, 0) AS present_count,
            COALESCE(attendance_counts.late_count, 0) AS late_count,
            COALESCE(attendance_counts.excused_count, 0) AS excused_count
        FROM events
        -- Aggregate RSVP responses first so the outer query can stay one row per event.
        LEFT JOIN (
            SELECT
                event_id,
                SUM(CASE WHEN status = 'yes' THEN 1 ELSE 0 END) AS yes_count,
                SUM(CASE WHEN status = 'maybe' THEN 1 ELSE 0 END) AS maybe_count,
                SUM(CASE WHEN status = 'no' THEN 1 ELSE 0 END) AS no_count
            FROM rsvps
            GROUP BY event_id
        ) AS rsvp_counts ON events.event_id = rsvp_counts.event_id
        -- Attendance is aggregated separately because it answers a different question than RSVP: who actually showed up.
        LEFT JOIN (
            SELECT
                event_id,
                SUM(CASE WHEN attendance_status = 'present' THEN 1 ELSE 0 END) AS present_count,
                SUM(CASE WHEN attendance_status = 'late' THEN 1 ELSE 0 END) AS late_count,
                SUM(CASE WHEN attendance_status = 'excused' THEN 1 ELSE 0 END) AS excused_count
            FROM attendance
            GROUP BY event_id
        ) AS attendance_counts ON events.event_id = attendance_counts.event_id
        ORDER BY events.event_date DESC, events.title ASC
        """
    )
    columns = [
        "event_id",
        "title",
        "event_date",
        "category",
        "rsvp_yes",
        "rsvp_maybe",
        "rsvp_no",
        "present_count",
        "late_count",
        "excused_count",
    ]
    return _as_dataframe(rows, columns)


def get_recent_attendance_df():
    """Return the most recent check-ins for a simple activity feed."""
    rows = fetch_all(
        """
        SELECT
            members.first_name || ' ' || members.last_name AS member_name,
            events.title AS event_title,
            attendance.attendance_status,
            attendance.checked_in_at
        FROM attendance
        JOIN members ON attendance.member_id = members.member_id
        JOIN events ON attendance.event_id = events.event_id
        ORDER BY attendance.checked_in_at DESC
        LIMIT 20
        """
    )
    columns = ["member_name", "event_title", "attendance_status", "checked_in_at"]
    return _as_dataframe(rows, columns)


def create_prospect(first_name, last_name, email, phone, major, class_year, interest_source, notes):
    """Create a prospect record from the public intake form."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO prospects (
                    first_name,
                    last_name,
                    email,
                    phone,
                    major,
                    class_year,
                    interest_source,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (first_name, last_name, email, phone, major, class_year, interest_source, notes),
            )
            conn.commit()
        return True, "Interest form submitted successfully."
    except sqlite3.IntegrityError:
        return False, "A prospect with this email already exists."


def create_member(first_name, last_name, email, phone, major, class_year, status, notes):
    """Create a member directly from the admin dashboard."""
    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO members (
                    first_name,
                    last_name,
                    email,
                    phone,
                    major,
                    class_year,
                    status,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (first_name, last_name, email, phone, major, class_year, status, notes),
            )
            conn.commit()
        return True, "Member created successfully."
    except sqlite3.IntegrityError:
        return False, "A member with this email already exists."


def convert_prospect_to_member(prospect_id, member_status):
    """Promote a prospect into a member and keep a link back to the original intake record."""
    with get_connection() as conn:
        prospect = conn.execute(
            "SELECT * FROM prospects WHERE prospect_id = ? AND status != 'converted'",
            (prospect_id,),
        ).fetchone()

        if not prospect:
            return False, "Prospect not found or already converted."

        try:
            # The conversion copies prospect data into members so the final member record can stand on its own if prospect handling changes later
            cursor = conn.execute(
                """
                INSERT INTO members (
                    first_name,
                    last_name,
                    email,
                    phone,
                    major,
                    class_year,
                    status,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    prospect["first_name"],
                    prospect["last_name"],
                    prospect["email"],
                    prospect["phone"],
                    prospect["major"],
                    prospect["class_year"],
                    member_status,
                    prospect["notes"],
                ),
            )
            member_id = cursor.lastrowid

            conn.execute(
                """
                UPDATE prospects
                SET status = 'converted', converted_member_id = ?
                WHERE prospect_id = ?
                """,
                (member_id, prospect_id),
            )
            conn.commit()
            return True, "Prospect converted into a member."
        except sqlite3.IntegrityError:
            return False, "This prospect email already belongs to a member."


def update_member_status(member_id, new_status):
    """Update a member's current status from the admin dashboard."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE members SET status = ? WHERE member_id = ?",
            (new_status, member_id),
        )
        conn.commit()
    return True, "Member status updated."


def delete_member(member_id):
    """Remove a member and clean up the records that depend on that member."""
    with get_connection() as conn:
        member = conn.execute(
            "SELECT first_name, last_name FROM members WHERE member_id = ?",
            (member_id,),
        ).fetchone()

        if not member:
            return False, "Member not found."

        # Remove child records first so the member row can be deleted without violating foreign key constraints.
        conn.execute("DELETE FROM attendance WHERE member_id = ?", (member_id,))
        conn.execute("DELETE FROM rsvps WHERE member_id = ?", (member_id,))

        # If this member came from a prospect, reopen that prospect record so the intake history is preserved instead of leaving a broken reference behind.
        conn.execute(
            """
            UPDATE prospects
            SET status = 'new', converted_member_id = NULL
            WHERE converted_member_id = ?
            """,
            (member_id,),
        )

        conn.execute("DELETE FROM members WHERE member_id = ?", (member_id,))
        conn.commit()

    full_name = f"{member['first_name']} {member['last_name']}"
    return True, f"Removed {full_name} and related records."


def create_event(title, description, event_date, start_time, end_time, location, category, is_required):
    """Create an event record that can later accept RSVP and attendance data."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO events (
                title,
                description,
                event_date,
                start_time,
                end_time,
                location,
                category,
                is_required
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, event_date, start_time, end_time, location, category, int(is_required)),
        )
        conn.commit()
    return True, "Event created successfully."


def submit_rsvp(email, event_id, status):
    """Store or update a member's RSVP for a specific event."""
    member = fetch_one(
        "SELECT member_id FROM members WHERE lower(email) = lower(?)",
        (email.strip(),),
    )
    if not member:
        return False, "Email not found. Ask an admin to create your member profile first."

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO rsvps (member_id, event_id, status)
            VALUES (?, ?, ?)
            -- A member should only have one RSVP per event, so repeat submissions
            -- overwrite the earlier choice instead of creating duplicates.
            ON CONFLICT(member_id, event_id)
            DO UPDATE SET
                status = excluded.status,
                responded_at = CURRENT_TIMESTAMP
            """,
            (member["member_id"], event_id, status),
        )
        conn.commit()
    return True, "RSVP saved successfully."


def check_in_member(email, event_id, attendance_status="present", check_in_method="self"):
    """Record attendance for a member at a specific event."""
    member = fetch_one(
        "SELECT member_id FROM members WHERE lower(email) = lower(?)",
        (email.strip(),),
    )
    if not member:
        return False, "Email not found. Ask an admin to create your member profile first."

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO attendance (member_id, event_id, attendance_status, check_in_method)
                VALUES (?, ?, ?, ?)
                """,
                (member["member_id"], event_id, attendance_status, check_in_method),
            )
            conn.commit()
        return True, "Check-in recorded successfully."
    except sqlite3.IntegrityError:
        return False, "This member has already checked into the selected event."