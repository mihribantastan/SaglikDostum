import sqlite3

DATABASE_NAME = 'eldercare.db'

def get_connection():
    return sqlite3.connect(DATABASE_NAME)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            role TEXT NOT NULL,
            address TEXT,
            emergency_contact TEXT
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            blood_pressure TEXT,
            heart_rate INTEGER,
            blood_sugar REAL,
            weight REAL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            start_date TEXT,
            end_date TEXT,
            instructions TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            reminder_time TEXT NOT NULL,
            repeat_interval TEXT,
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')

    conn.commit()
    conn.close()

def execute_query(query, params=None, fetchone=False, fetchall=False):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        if fetchone:
            return cursor.fetchone()
        elif fetchall:
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        return True
    except sqlite3.Error as e:
        print(f"Veritabanı hatası: {e}")
        return False
    finally:
        conn.close()

def fetch_one(query, params=None):
    return execute_query(query, params, fetchone=True)

def fetch_all(query, params=None):
    return execute_query(query, params, fetchall=True)