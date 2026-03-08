import streamlit as st
import sqlite3
import pandas as pd

# --- DATABASE FUNCTIONS (The Logic Layer) ---

def get_attendance_roster():
    conn = sqlite3.connect('club_hub.db')
    query = '''
        SELECT 
            members.first_name || ' ' || members.last_name AS "Student Name",
            members.major AS "Major",
            events.title AS "Event Attended",
            events.event_date AS "Date"
        FROM attendance
        JOIN members ON attendance.member_id = members.member_id
        JOIN events ON attendance.event_id = events.event_id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_new_member(first_name, last_name, email, major):
    conn = sqlite3.connect('club_hub.db')
    cursor = conn.cursor()
    
    try:
        # Parameterized query to prevent SQL Injection
        cursor.execute('''
            INSERT INTO members (first_name, last_name, email, major, status)
            VALUES (?, ?, ?, ?, 'Active')
        ''', (first_name, last_name, email, major))
        conn.commit()
        return True, "Success: Student added to the database!"
    except sqlite3.IntegrityError:
        # This catches the UNIQUE constraint error we set up in our schema!
        return False, "Error: A student with this email already exists in the system."
    except Exception as e:
        return False, f"An unexpected error occurred: {e}"
    finally:
        conn.close()

# --- STREAMLIT UI (The Presentation Layer) ---

st.set_page_config(page_title="ClubHub Dashboard", layout="wide")

# 1. The Sidebar Form (Data Input)
with st.sidebar:
    st.header("+ Add New Member")
    st.write("Register a new student into the system.")
    
    # clear_on_submit empties the text boxes after a successful save
    with st.form("new_member_form", clear_on_submit=True):
        f_name = st.text_input("First Name *")
        l_name = st.text_input("Last Name *")
        email_input = st.text_input("School Email *")
        
        # A dropdown menu for structured data
        major_input = st.selectbox(
            "Major", 
            ["Computer Science", "Electrical Engineering", "Mechanical Engineering", "Business", "Undeclared"]
        )
        
        submit_btn = st.form_submit_button("Register Student")
        
        # 2. Form Validation & Submission Logic
        if submit_btn:
            if not f_name or not l_name or not email_input:
                st.warning("Please fill out all required fields (*).")
            else:
                success, message = add_new_member(f_name, l_name, email_input, major_input)
                if success:
                    st.success(message)
                else:
                    st.error(message)



# 3. The Main Dashboard (Data Output)
st.title("ClubHub Admin Dashboard")
st.write("A centralized relational database system for student organizations.")
st.divider()

st.subheader("Master Attendance Roster")

# Fetch and display the live data
roster_df = get_attendance_roster()
st.dataframe(roster_df, use_container_width=True, hide_index=True)