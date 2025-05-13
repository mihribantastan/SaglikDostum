from database import execute_query, fetch_all

def add_medication(user_id, name, dosage, frequency, start_date, end_date, instructions):
    query = '''
        INSERT INTO medications (user_id, name, dosage, frequency, start_date, end_date, instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    return execute_query(query, (user_id, name, dosage, frequency, start_date, end_date, instructions))

def get_active_medications(user_id, now):
    query = '''
        SELECT * FROM medications
        WHERE user_id = ?
        AND start_date <= ?
        AND end_date >= ?
        ORDER BY name
    '''
    return fetch_all(query, (user_id, now, now))

def get_medications(user_id):
    query = '''
        SELECT * FROM medications
        WHERE user_id = ?
        ORDER BY start_date DESC
    '''
    return fetch_all(query, (user_id,))