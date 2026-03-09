import streamlit as st

from services import RSVP_STATUSES, check_in_member, create_prospect, get_upcoming_events, submit_rsvp


def format_event(row):
    """Build one readable label for event dropdowns in the member portal."""
    time_text = f" at {row['start_time']}" if row["start_time"] else ""
    location_text = f" - {row['location']}" if row["location"] else ""
    return f"{row['title']} ({row['event_date']}{time_text}{location_text})"


st.set_page_config(page_title="ClubHub Portal", layout="centered")

st.title("ClubHub Member Portal")
st.write("Submit interest, RSVP for upcoming events, and check in when you arrive.")

# The portal reuses one event list for both RSVP and check-in so members see a consistent set of upcoming choices everywhere.
upcoming_events = get_upcoming_events()

st.subheader("Upcoming Events")
if upcoming_events:
    st.dataframe(upcoming_events, use_container_width=True, hide_index=True)
else:
    st.info("No upcoming events are available yet.")

prospect_tab, rsvp_tab, checkin_tab = st.tabs(["Express Interest", "RSVP", "Check In"])

with prospect_tab:
    st.subheader("Prospect Intake")
    with st.form("prospect_form", clear_on_submit=True):
        intake_col1, intake_col2 = st.columns(2)
        with intake_col1:
            first_name = st.text_input("First Name *")
            email = st.text_input("Email *")
            major = st.text_input("Major")
            interest_source = st.text_input("How did you hear about us?")
        with intake_col2:
            last_name = st.text_input("Last Name *")
            phone = st.text_input("Phone")
            class_year = st.text_input("Grad Year")
            notes = st.text_area("Notes")

        submit_prospect = st.form_submit_button("Submit Interest Form")
        if submit_prospect:
            if not first_name or not last_name or not email:
                st.warning("First name, last name, and email are required.")
            else:
                success, message = create_prospect(
                    first_name,
                    last_name,
                    email,
                    phone,
                    major,
                    class_year,
                    interest_source,
                    notes,
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

with rsvp_tab:
    st.subheader("Event RSVP")
    if not upcoming_events:
        st.info("There are no upcoming events to RSVP for yet.")
    else:
        with st.form("rsvp_form", clear_on_submit=True):
            # RSVP is limited to existing members. Prospects can express interest, but admins decide when a person becomes a member.
            member_email = st.text_input("Member Email")
            selected_event = st.selectbox(
                "Select Event",
                options=upcoming_events,
                format_func=format_event,
            )
            selected_rsvp = st.selectbox("RSVP", options=RSVP_STATUSES, format_func=str.title)

            submit_rsvp_button = st.form_submit_button("Save RSVP")
            if submit_rsvp_button:
                if not member_email:
                    st.warning("Email is required.")
                else:
                    success, message = submit_rsvp(member_email, selected_event["event_id"], selected_rsvp)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

with checkin_tab:
    st.subheader("Attendance Check-In")
    if not upcoming_events:
        st.info("There are no upcoming events to check into yet.")
    else:
        with st.form("check_in_form", clear_on_submit=True):
            # intentionally simple, identify the member, pick the event, and record attendance with one submit
            attendee_email = st.text_input("Member Email")
            selected_event = st.selectbox(
                "Select Event",
                options=upcoming_events,
                format_func=format_event,
                key="check_in_event",
            )
            submit_check_in = st.form_submit_button("Check In")

            if submit_check_in:
                if not attendee_email:
                    st.warning("Email is required.")
                else:
                    success, message = check_in_member(attendee_email, selected_event["event_id"])
                    if success:
                        st.success(message)
                    else:
                        st.error(message)