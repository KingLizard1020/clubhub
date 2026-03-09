-- Members are official organization participants. Their current status powers
-- admin management, RSVP eligibility, and attendance tracking.
CREATE TABLE IF NOT EXISTS members (
    member_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    major TEXT,
    class_year TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    joined_at DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Prospects are kept separate from members so organizations can collect interest
-- first and only convert people into members when appropriate.
CREATE TABLE IF NOT EXISTS prospects (
    prospect_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    major TEXT,
    class_year TEXT,
    interest_source TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    converted_member_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (converted_member_id) REFERENCES members (member_id)
);

-- Events are the shared anchor for RSVP and attendance records.
CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    start_time TEXT,
    end_time TEXT,
    location TEXT,
    category TEXT NOT NULL DEFAULT 'other',
    is_required INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- RSVP stores intent before an event happens.
CREATE TABLE IF NOT EXISTS rsvps (
    rsvp_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    responded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (member_id),
    FOREIGN KEY (event_id) REFERENCES events (event_id),
    UNIQUE(member_id, event_id)
);

-- Attendance stores what actually happened at the event.
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    attendance_status TEXT NOT NULL DEFAULT 'present',
    check_in_method TEXT NOT NULL DEFAULT 'self',
    checked_in_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members (member_id),
    FOREIGN KEY (event_id) REFERENCES events (event_id),
    UNIQUE(member_id, event_id)
);

-- A few focused indexes
CREATE INDEX IF NOT EXISTS idx_members_email ON members(email);
CREATE INDEX IF NOT EXISTS idx_prospects_status ON prospects(status);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_rsvps_event_id ON rsvps(event_id);
CREATE INDEX IF NOT EXISTS idx_attendance_event_id ON attendance(event_id);