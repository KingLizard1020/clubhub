import streamlit as st
import sqlite3
import pandas as pd

# --- DATABASE FUNCTIONS ---

def get_events():
    """Fetches upcoming events for the dropdown menu."""
    conn = sqlite3.connect('club_hub.db')
    df = pd.read_sql_query("SELECT event_id, title, event_date FROM events", conn)
    conn.close()
    return df

def add_new_member(first_name, last_name, email, major):
    """Registers a new student."""
    conn = sqlite3.connect('club_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO members (first_name, last_name, email, major)
            VALUES (?, ?, ?, ?)
        ''', (first_name, last_name, email, major))
        conn.commit()
        return True, "Welcome to the club! Your profile has been created."
    except sqlite3.IntegrityError:
        return False, "An account with this email already exists."
    finally:
        conn.close()

def log_attendance(email, event_id):
    """Logs a student into an event using their email."""
    conn = sqlite3.connect('club_hub.db')
    cursor = conn.cursor()
    try:
        # 1. Look up the student's ID using their email
        cursor.execute("SELECT member_id FROM members WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        if not result:
            return False, "Email not found. Please register as a new member first!"
        
        member_id = result[0]
        
        # 2. Log the attendance
        cursor.execute('''
            INSERT INTO attendance (member_id, event_id)
            VALUES (?, ?)
        ''', (member_id, event_id))
        conn.commit()
        return True, "Successfully checked in! Enjoy the event."
        
    except sqlite3.IntegrityError:
        return False, "You have already checked into this event."
    finally:
        conn.close()

# --- STREAMLIT UI ---

st.set_page_config(page_title="Club Portal", layout="centered")

st.title("Student Organization Portal")
st.write("Welcome! Use this portal to join the organization or check into today's event.")

# Fetch events for the check-in dropdown
events_df = get_events()

# Create two separate tabs for the user experience
tab1, tab2 = st.tabs(["Check Into an Event", "Join the Club (New Members)"])

# --- TAB 1: Event Check-In ---
with tab1:
    st.subheader("Event Check-In")
    st.write("Already a member? Enter your email to log your attendance.")
    
    with st.form("check_in_form", clear_on_submit=True):
        student_email = st.text_input("School Email")
        
        # Create a dictionary to map Event Titles to Event IDs for the database
        event_dict = dict(zip(events_df['title'], events_df['event_id']))
        selected_event_title = st.selectbox("Select Event", options=event_dict.keys())
        
        submit_attendance = st.form_submit_button("Check In")
        
        if submit_attendance:
            if not student_email:
                st.warning("Please enter your email.")
            else:
                event_id = event_dict[selected_event_title]
                success, message = log_attendance(student_email, event_id)
                if success:
                    st.success(message)
                else:
                    st.error(message)

# --- TAB 2: New Member Onboarding ---
with tab2:
    st.subheader("New Member Registration")
    
    with st.form("new_member_form", clear_on_submit=True):
        f_name = st.text_input("First Name")
        l_name = st.text_input("Last Name")
        new_email = st.text_input("School Email")
        major = st.selectbox("Major", ["Computer Science", "Electrical Engineering", "Other"])
        
        submit_new = st.form_submit_button("Register Profile")
        
        if submit_new:
            if not f_name or not l_name or not new_email:
                st.warning("Please fill out all fields.")
            else:
                success, message = add_new_member(f_name, l_name, new_email, major)
                if success:
                    st.success(message)
                    st.info("You can now head over to the 'Check Into an Event' tab!")
                else:
                    st.error(message)