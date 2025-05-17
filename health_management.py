from database import execute_query, fetch_one, fetch_all

def add_health_data(user_id, blood_pressure, heart_rate, blood_sugar, weight, notes):
    query = '''
        INSERT INTO health_data (user_id, blood_pressure, heart_rate, blood_sugar, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    return execute_query(query, (user_id, blood_pressure, heart_rate, blood_sugar, weight, notes))

def get_latest_health_data(user_id):
    query = '''
        SELECT * FROM health_data
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    '''
    return fetch_one(query, (user_id,))

def get_health_history(user_id):
    query = '''
        SELECT * FROM health_data
        WHERE user_id = ?
        ORDER BY timestamp DESC
    '''
    return fetch_all(query, (user_id,))