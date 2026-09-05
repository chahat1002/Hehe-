import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports.db')

def seed():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            severity TEXT NOT NULL,
            category TEXT,
            description TEXT,
            timestamp TEXT
        )
    ''')
    
    # Sample mock reports
    sample_reports = [
        (28.6139, 77.2090, 'High', 'Assault,No CCTV', 'Reported harassment near Central Delhi junction late at night.', '10:45 PM'),
        (28.6250, 77.2150, 'Medium', 'Poor lighting,Isolated area', 'Street lights malfunctioning on this stretch for over a week.', '09:15 PM'),
        (28.6020, 77.2250, 'Low', 'Accident-prone', 'Narrow intersection with high traffic during rush hours.', '07:30 PM')
    ]
    
    cursor.executemany('''
        INSERT INTO reports (lat, lng, severity, category, description, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', sample_reports)
    
    conn.commit()
    conn.close()
    print(f" Successfully seeded {len(sample_reports)} reports into {DB_FILE}!")

if __name__ == '__main__':
    seed()
