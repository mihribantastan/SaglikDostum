from database import execute_query, fetch_all
from datetime import datetime

def add_reminder(user_id, title, description, reminder_time, repeat_interval):
    query = '''
        INSERT INTO reminders (user_id, title, description, reminder_time, repeat_interval)
        VALUES (?, ?, ?, ?, ?)
    '''
    return execute_query(query, (user_id, title, description, reminder_time, repeat_interval))

def get_upcoming_reminders(user_id, now):
    query = '''
        SELECT * FROM reminders
        WHERE user_id = ?
        AND reminder_time >= ?
        AND is_completed = 0
        ORDER BY reminder_time
        LIMIT 5
    '''
    return fetch_all(query, (user_id, now,))

def get_reminders(user_id):
    query = '''
        SELECT * FROM reminders
        WHERE user_id = ?
        ORDER BY reminder_time DESC
    '''
    return fetch_all(query, (user_id,))

def mark_reminder_completed(reminder_id):
    query = "UPDATE reminders SET is_completed = 1 WHERE id = ?"
    return execute_query(query, (reminder_id,))