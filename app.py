import streamlit as st

from services import (
    EVENT_CATEGORIES,
    MEMBER_STATUSES,
    convert_prospect_to_member,
    create_event,
    create_member,
    delete_member,
    get_dashboard_summary,
    get_event_summary_df,
    get_members_df,
    get_pending_prospects_df,
    get_recent_attendance_df,
    get_upcoming_events_df,
    update_member_status,
)


def format_status(value):
    """Turn stored values like 'active' into labels that read well in the UI."""
    return value.replace("_", " ").title()


st.set_page_config(page_title="ClubHub Admin Dashboard", layout="wide")

st.title("ClubHub Admin Dashboard")
st.write("Manage prospects, members, events, RSVP activity, and attendance in one place.")
st.divider()

# system snapshot before scroll into the management tables below
summary = get_dashboard_summary()
metric_cols = st.columns(4)
metric_cols[0].metric("Open Prospects", summary["open_prospects"])
metric_cols[1].metric("Active Members", summary["active_members"])
metric_cols[2].metric("Upcoming Events", summary["upcoming_events"])
metric_cols[3].metric("Total Check-Ins", summary["total_check_ins"])

overview_tab, prospects_tab, members_tab, events_tab, attendance_tab = st.tabs(
    ["Overview", "Prospects", "Members", "Events", "Attendance"]
)

with overview_tab:
    # The overview combines a few small tables instead of trying to show every record on the landing view
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Upcoming Events")
        upcoming_events_df = get_upcoming_events_df()
        st.dataframe(upcoming_events_df, use_container_width=True, hide_index=True)

    with right_col:
        st.subheader("Recent Check-Ins")
        recent_attendance_df = get_recent_attendance_df()
        st.dataframe(recent_attendance_df, use_container_width=True, hide_index=True)

    st.subheader("Event Summary")
    event_summary_df = get_event_summary_df()
    st.dataframe(event_summary_df, use_container_width=True, hide_index=True)

with prospects_tab:
    st.subheader("Pending Prospects")
    prospects_df = get_pending_prospects_df()
    st.dataframe(prospects_df, use_container_width=True, hide_index=True)

    if prospects_df.empty:
        st.info("No open prospects are waiting for review.")
    else:
        # Streamlit selectboxes work well with a list of dictionaries here because the UI needs both a readable label and the underlying prospect_id.
        prospect_options = prospects_df.to_dict("records")
        with st.form("convert_prospect_form"):
            selected_prospect = st.selectbox(
                "Convert Prospect",
                options=prospect_options,
                format_func=lambda row: f"{row['name']} ({row['email']})",
            )
            selected_status = st.selectbox(
                "New Member Status",
                options=MEMBER_STATUSES,
                format_func=format_status,
            )
            convert_button = st.form_submit_button("Convert to Member")

            if convert_button:
                success, message = convert_prospect_to_member(
                    selected_prospect["prospect_id"],
                    selected_status,
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

with members_tab:
    st.subheader("Create Member")
    with st.form("create_member_form", clear_on_submit=True):
        # Two columns keep the form compact without hiding fields in accordions.
        member_col1, member_col2 = st.columns(2)
        with member_col1:
            first_name = st.text_input("First Name *")
            email = st.text_input("Email *")
            major = st.text_input("Major")
            status = st.selectbox("Status", options=MEMBER_STATUSES, format_func=format_status)
        with member_col2:
            last_name = st.text_input("Last Name *")
            phone = st.text_input("Phone")
            class_year = st.text_input("Class Year")
            notes = st.text_area("Notes")

        create_member_button = st.form_submit_button("Create Member")
        if create_member_button:
            if not first_name or not last_name or not email:
                st.warning("First name, last name, and email are required.")
            else:
                success, message = create_member(
                    first_name,
                    last_name,
                    email,
                    phone,
                    major,
                    class_year,
                    status,
                    notes,
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.subheader("Current Members")
    members_df = get_members_df()
    st.dataframe(members_df, use_container_width=True, hide_index=True)

    if not members_df.empty:
        # Reuse the table rows as select options so status updates stay tied to the exact member_id shown in the admin list.
        member_options = members_df.to_dict("records")
        with st.form("update_member_status_form"):
            selected_member = st.selectbox(
                "Select Member",
                options=member_options,
                format_func=lambda row: f"{row['name']} ({row['status']})",
            )
            updated_status = st.selectbox(
                "Updated Status",
                options=MEMBER_STATUSES,
                format_func=format_status,
            )
            update_status_button = st.form_submit_button("Update Status")

            if update_status_button:
                success, message = update_member_status(selected_member["member_id"], updated_status)
                if success:
                    st.success(message)
                else:
                    st.error(message)

        st.subheader("Remove Member")
        with st.form("remove_member_form"):
            member_to_remove = st.selectbox(
                "Member To Remove",
                options=member_options,
                format_func=lambda row: f"{row['name']} ({row['email']})",
            )
            confirm_remove = st.checkbox(
                "I understand this will remove the member and their RSVP and attendance records."
            )
            remove_member_button = st.form_submit_button("Remove Member")

            if remove_member_button:
                if not confirm_remove:
                    st.warning("Please confirm the removal before continuing.")
                else:
                    success, message = delete_member(member_to_remove["member_id"])
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

with events_tab:
    st.subheader("Create Event")
    with st.form("create_event_form", clear_on_submit=True):
        event_col1, event_col2 = st.columns(2)
        with event_col1:
            title = st.text_input("Title *")
            event_date = st.date_input("Event Date")
            start_time = st.time_input("Start Time")
            location = st.text_input("Location")
        with event_col2:
            category = st.selectbox("Category", options=EVENT_CATEGORIES, format_func=format_status)
            end_time = st.time_input("End Time")
            is_required = st.checkbox("Required Event")
            description = st.text_area("Description")

        create_event_button = st.form_submit_button("Create Event")
        if create_event_button:
            if not title:
                st.warning("Event title is required.")
            else:
                # Streamlit returns date and time objects, so convert them to plain strings before storing them in SQLite.
                success, message = create_event(
                    title,
                    description,
                    event_date.isoformat(),
                    start_time.strftime("%H:%M"),
                    end_time.strftime("%H:%M"),
                    location,
                    category,
                    is_required,
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.subheader("Upcoming Event List")
    upcoming_events_df = get_upcoming_events_df()
    st.dataframe(upcoming_events_df, use_container_width=True, hide_index=True)

with attendance_tab:
    st.subheader("RSVP and Attendance by Event")
    event_summary_df = get_event_summary_df()
    st.dataframe(event_summary_df, use_container_width=True, hide_index=True)

    st.subheader("Recent Attendance Activity")
    recent_attendance_df = get_recent_attendance_df()
    st.dataframe(recent_attendance_df, use_container_width=True, hide_index=True)