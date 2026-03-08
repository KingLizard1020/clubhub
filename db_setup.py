import sqlite3

def setup_database():
    # 1. Connect to the database (creates the file if it doesn't exist)
    conn = sqlite3.connect('club_hub.db')
    cursor = conn.cursor()

    # 2. Read the SQL schema file
    with open('schema.sql', 'r') as file:
        sql_script = file.read()

    # 3. Execute the SQL script
    cursor.executescript(sql_script)

    # 4. Save (commit) the changes and close the connection
    conn.commit()
    conn.close()

    print("Success: Database 'club_hub.db' created and tables initialized!")

if __name__ == "__main__":
    setup_database()