import hashlib
from database import fetch_one, execute_query

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed_password):
    return hash_password(password) == hashed_password

def get_user_by_username(username):
    query = "SELECT * FROM users WHERE username = ?"
    return fetch_one(query, (username,))

def register_user(username, password, full_name, email, phone, role):
    hashed_password = hash_password(password)
    query = '''
        INSERT INTO users (username, password, full_name, email, phone, role)
        VALUES (?, ?, ?, ?, ?, ?)
    '''
    return execute_query(query, (username, hashed_password, full_name, email, phone, role))

def update_user_profile(user_id, full_name, email, phone, address, emergency_contact):
    query = '''
        UPDATE users SET
            full_name = ?,
            email = ?,
            phone = ?,
            address = ?,
            emergency_contact = ?
        WHERE id = ?
    '''
    return execute_query(query, (full_name, email, phone, address, emergency_contact, user_id))