from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'

DATABASE = 'eldercare.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    if conn:
        conn.close()

def query_db(query, args=(), one=False):
    conn = get_db()
    cursor = conn.execute(query, args)
    results = cursor.fetchall()
    close_db(conn)
    return (results[0] if results else None) if one else results

def execute_db(query, args=()):
    conn = get_db()
    cursor = conn.execute(query, args)
    conn.commit()
    close_db(conn)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed_password):
    return hash_password(password) == hashed_password

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    error = None
    user = query_db('SELECT * FROM users WHERE username = ?', [username], one=True)

    if user is None:
        error = 'Geçersiz kullanıcı adı'
    elif not check_password(password, user['password']):
        error = 'Geçersiz şifre'

    if error:
        return render_template('login.html', error=error)
    else:
        session['user_id'] = user['id']
        return redirect(url_for('dashboard'))

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    role = request.form['role']
    error = None

    if not username or not password:
        error = 'Kullanıcı adı ve şifre gereklidir'
    elif password != confirm_password:
        error = 'Şifreler eşleşmiyor'
    elif query_db('SELECT id FROM users WHERE username = ?', [username], one=True):
        error = 'Bu kullanıcı adı zaten alınmış'

    if error:
        return render_template('register.html', error=error)
    else:
        hashed_password = hash_password(password)
        execute_db('''
            INSERT INTO users (username, password, full_name, email, phone, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [username, hashed_password, full_name, email, phone, role])
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    user = query_db('SELECT full_name FROM users WHERE id = ?', [user_id], one=True)
    health_data = query_db('''
        SELECT blood_pressure, heart_rate, blood_sugar, weight
        FROM health_data WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1
    ''', [user_id], one=True)
    reminders = query_db('''
        SELECT title, reminder_time FROM reminders
        WHERE user_id = ? AND reminder_time > datetime('now') AND is_completed = 0
        ORDER BY reminder_time LIMIT 3
    ''', [user_id])
    medications = query_db('''
        SELECT name, dosage FROM medications
        WHERE user_id = ? AND start_date <= datetime('now') AND end_date >= datetime('now')
        ORDER BY name LIMIT 3
    ''', [user_id])
    return render_template('dashboard.html', user=user, health_data=health_data, reminders=reminders, medications=medications)

@app.route('/health')
def health_page():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    health_history = query_db('SELECT * FROM health_data WHERE user_id = ? ORDER BY timestamp DESC', [user_id])
    return render_template('health.html', health_history=health_history)

@app.route('/add_health', methods=['POST'])
def add_health():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    blood_pressure = request.form['blood_pressure']
    heart_rate = request.form['heart_rate']
    blood_sugar = request.form['blood_sugar']
    weight = request.form['weight']
    notes = request.form['notes']

    execute_db('''
        INSERT INTO health_data (user_id, blood_pressure, heart_rate, blood_sugar, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', [user_id, blood_pressure, heart_rate, blood_sugar, weight, notes])
    return redirect(url_for('health_page'))

@app.route('/medications')
def medications_page():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    medications = query_db('SELECT * FROM medications WHERE user_id = ? ORDER BY start_date DESC', [user_id])
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    thirty_days_later = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M")
    return render_template('medications.html', medications=medications, now=now, thirty_days_later=thirty_days_later)

@app.route('/add_medication', methods=['POST'])
def add_medication():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    name = request.form['name']
    dosage = request.form['dosage']
    frequency = request.form['frequency']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    instructions = request.form['instructions']

    execute_db('''
        INSERT INTO medications (user_id, name, dosage, frequency, start_date, end_date, instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [user_id, name, dosage, frequency, start_date, end_date, instructions])
    return redirect(url_for('medications_page'))

@app.route('/reminders')
def reminders_page():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    reminders = query_db('SELECT * FROM reminders WHERE user_id = ? ORDER BY reminder_time DESC', [user_id])
    now_plus_hour = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    return render_template('reminders.html', reminders=reminders, now_plus_hour=now_plus_hour)

@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    title = request.form['title']
    description = request.form['description']
    reminder_time_str = request.form['reminder_time']
    repeat_interval = request.form['repeat_interval']

    try:
        reminder_time = datetime.strptime(reminder_time_str, "%Y-%m-%d %H:%M")
        execute_db('''
            INSERT INTO reminders (user_id, title, description, reminder_time, repeat_interval)
            VALUES (?, ?, ?, ?, ?)
        ''', [user_id, title, description, reminder_time, repeat_interval])
    except ValueError:
        pass

    return redirect(url_for('reminders_page'))

@app.route('/profile')
def profile_page():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    user = query_db('SELECT username, full_name, email, phone, role FROM users WHERE id = ?', [user_id], one=True)
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']

    execute_db('''
        UPDATE users SET full_name = ?, email = ?, phone = ? WHERE id = ?
    ''', [full_name, email, phone, user_id])
    return render_template('profile.html', user=query_db('SELECT username, full_name, email, phone, role FROM users WHERE id = ?', [user_id], one=True), message='Profil başarıyla güncellendi!')

@app.route('/change_password', methods=['POST'])
def change_password():
    if not session.get('user_id'):
        return redirect(url_for('index'))
    user_id = session['user_id']
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    confirm_new_password = request.form['confirm_new_password']
    error = None

    user = query_db('SELECT password FROM users WHERE id = ?', [user_id], one=True)
    if not user or not check_password(old_password, user['password']):
        error = 'Eski şifre yanlış'
    elif new_password != confirm_new_password:
        error = 'Yeni şifreler eşleşmiyor'
    elif len(new_password) < 6: # Basit bir şifre kontrolü
        error = 'Yeni şifre en az 6 karakter olmalı'

    if error:
        return render_template('profile.html', user=query_db('SELECT username, full_name, email, phone, role FROM users WHERE id = ?', [user_id], one=True), password_error=error)
    else:
        hashed_new_password = hash_password(new_password)
        execute_db('UPDATE users SET password = ? WHERE id = ?', [hashed_new_password, user_id])
        return render_template('profile.html', user=query_db('SELECT username, full_name, email, phone, role FROM users WHERE id = ?', [user_id], one=True), message='Şifre başarıyla değiştirildi!')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)