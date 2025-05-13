import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import hashlib
from threading import Timer
from datetime import datetime as dt

class ElderCareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yaşlı Takip Sistemi")
        self.root.geometry("1000x700")
        self.current_user = None
        self.reminder_timers = []
        
        # Veritabanı bağlantısı
        self.db_connection = sqlite3.connect('eldercare.db')
        self.create_tables()
        
        self.setup_ui()
        self.load_reminders()

    def create_tables(self):
        cursor = self.db_connection.cursor()
        
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
        
        self.db_connection.commit()

    def setup_ui(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.show_login_screen()
    
    def show_login_screen(self):
        self.clear_main_frame()
        
        login_frame = ttk.Frame(self.main_frame, padding="20 10 20 10")
        login_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(login_frame, text="Kullanıcı Adı:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Şifre:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(login_frame, text="Giriş Yap", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(login_frame, text="Kayıt Ol", command=self.show_register_screen).grid(row=3, column=0, columnspan=2)

    def show_register_screen(self):
        self.clear_main_frame()
        
        register_frame = ttk.Frame(self.main_frame, padding="20 10 20 10")
        register_frame.pack(fill=tk.BOTH, expand=True)
        
        entries = {}
        labels = ["Kullanıcı Adı", "Şifre", "Şifre Tekrar", "Tam Ad", "Email", "Telefon"]
        for i, label in enumerate(labels):
            ttk.Label(register_frame, text=label+":").grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            entries[label] = ttk.Entry(register_frame)
            entries[label].grid(row=i, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Rol:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        role_var = tk.StringVar(value="elder")
        ttk.Combobox(register_frame, textvariable=role_var, values=["elder", "relative"]).grid(row=6, column=1, padx=5, pady=5)
        
        ttk.Button(register_frame, text="Kayıt Ol", command=lambda: self.register(
            entries["Kullanıcı Adı"].get(),
            entries["Şifre"].get(),
            entries["Şifre Tekrar"].get(),
            entries["Tam Ad"].get(),
            entries["Email"].get(),
            entries["Telefon"].get(),
            role_var.get()
        )).grid(row=7, column=0, columnspan=2, pady=10)
        
        ttk.Button(register_frame, text="Geri", command=self.show_login_screen).grid(row=8, column=0, columnspan=2)

    def show_elder_dashboard(self):
        self.clear_main_frame()
        
        main_frame = ttk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çerçevesi
        menu_frame = ttk.Frame(main_frame, width=150, relief=tk.RIDGE, padding="10 5 10 5")
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(menu_frame, text=f"Hoş geldiniz,\n{self.current_user['full_name']}", 
                 font=('Helvetica', 10, 'bold')).pack(pady=10)
        
        buttons = [
            ("Ana Sayfa", self.show_elder_dashboard),
            ("Sağlık Bilgileri", self.show_health_info),
            ("İlaçlarım", self.show_medications),
            ("Hatırlatıcılar", self.show_reminders),
            ("Profil", self.show_profile),
            ("Çıkış Yap", self.logout)
        ]
        
        for text, cmd in buttons:
            ttk.Button(menu_frame, text=text, command=cmd, width=15).pack(pady=3)
        
        # İçerik çerçevesi
        content_frame = ttk.Frame(main_frame, padding="15 10 15 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Özet Bilgiler", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        # Son sağlık verileri
        health_data = self.get_latest_health_data()
        if health_data:
            health_frame = ttk.LabelFrame(content_frame, text="Son Sağlık Ölçümleri", padding="10")
            health_frame.pack(fill=tk.X, pady=5)
            
            labels = [
                f"Kan Basıncı: {health_data['blood_pressure'] or 'N/A'}",
                f"Nabız: {health_data['heart_rate'] or 'N/A'}",
                f"Kan Şekeri: {health_data['blood_sugar'] or 'N/A'}",
                f"Kilo: {health_data['weight'] or 'N/A'}"
            ]
            for label in labels:
                ttk.Label(health_frame, text=label).pack(anchor=tk.W)
        
        # Yaklaşan hatırlatıcılar
        reminders = self.get_upcoming_reminders()
        if reminders:
            rem_frame = ttk.LabelFrame(content_frame, text="Yaklaşan Hatırlatıcılar", padding="10")
            rem_frame.pack(fill=tk.X, pady=5)
            
            for rem in reminders[:3]:  # En fazla 3 hatırlatıcı göster
                time = dt.strptime(rem['reminder_time'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
                ttk.Label(rem_frame, text=f"{rem['title']} - {time}").pack(anchor=tk.W)
        
        # Aktif ilaçlar
        meds = self.get_active_medications()
        if meds:
            med_frame = ttk.LabelFrame(content_frame, text="Aktif İlaçlar", padding="10")
            med_frame.pack(fill=tk.X, pady=5)
            
            for med in meds[:3]:  # En fazla 3 ilaç göster
                ttk.Label(med_frame, text=f"{med['name']} - {med['dosage']}").pack(anchor=tk.W)

    def show_health_info(self):
        self.clear_main_frame()
        self.create_menu_frame()
        
        content_frame = ttk.Frame(self.main_frame, padding="15 10 15 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Sağlık Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        # Yeni ölçüm formu
        add_frame = ttk.LabelFrame(content_frame, text="Yeni Ölçüm Ekle", padding="10")
        add_frame.pack(fill=tk.X, pady=5)
        
        fields = ["Kan Basıncı", "Nabız", "Kan Şekeri", "Kilo", "Notlar"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(add_frame, text=field+":").grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            entries[field] = ttk.Entry(add_frame)
            entries[field].grid(row=i, column=1, padx=5, pady=2)
        
        ttk.Button(add_frame, text="Kaydet", command=lambda: self.add_health_data(
            entries["Kan Basıncı"].get(),
            entries["Nabız"].get(),
            entries["Kan Şekeri"].get(),
            entries["Kilo"].get(),
            entries["Notlar"].get()
        )).grid(row=len(fields), column=0, columnspan=2, pady=5)
        
        # Ölçüm geçmişi
        history_frame = ttk.LabelFrame(content_frame, text="Ölçüm Geçmişi", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tree = ttk.Treeview(history_frame, columns=("Tarih", "Kan Basıncı", "Nabız", "Kan Şekeri", "Kilo"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        vsb = ttk.Scrollbar(history_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill=tk.BOTH, expand=True)
        
        for data in self.get_health_history():
            tree.insert("", tk.END, values=(
                data['timestamp'][:16],
                data['blood_pressure'] or "-",
                data['heart_rate'] or "-",
                data['blood_sugar'] or "-",
                data['weight'] or "-"
            ))

    def show_medications(self):
        self.clear_main_frame()
        self.create_menu_frame()
        
        content_frame = ttk.Frame(self.main_frame, padding="15 10 15 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="İlaçlarım", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        # Yeni ilaç formu
        add_frame = ttk.LabelFrame(content_frame, text="Yeni İlaç Ekle", padding="10")
        add_frame.pack(fill=tk.X, pady=5)
        
        fields = ["İlaç Adı", "Dozaj", "Sıklık", "Başlangıç", "Bitiş", "Talimatlar"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(add_frame, text=field+":").grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            entries[field] = ttk.Entry(add_frame)
            entries[field].grid(row=i, column=1, padx=5, pady=2)
        
        # Varsayılan değerler
        entries["Sıklık"].insert(0, "günlük")
        entries["Başlangıç"].insert(0, dt.now().strftime("%Y-%m-%d %H:%M"))
        entries["Bitiş"].insert(0, (dt.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M"))
        
        ttk.Button(add_frame, text="Ekle", command=lambda: self.add_medication(
            entries["İlaç Adı"].get(),
            entries["Dozaj"].get(),
            entries["Sıklık"].get(),
            entries["Başlangıç"].get(),
            entries["Bitiş"].get(),
            entries["Talimatlar"].get()
        )).grid(row=len(fields), column=0, columnspan=2, pady=5)
        
        # İlaç listesi
        list_frame = ttk.LabelFrame(content_frame, text="İlaç Listesi", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tree = ttk.Treeview(list_frame, columns=("İlaç", "Dozaj", "Sıklık", "Başlangıç", "Bitiş"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill=tk.BOTH, expand=True)
        
        for med in self.get_medications():
            tree.insert("", tk.END, values=(
                med['name'],
                med['dosage'] or "-",
                med['frequency'] or "-",
                med['start_date'][:16],
                med['end_date'][:16]
            ))

    def show_reminders(self):
        self.clear_main_frame()
        self.create_menu_frame()
        
        content_frame = ttk.Frame(self.main_frame, padding="15 10 15 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Hatırlatıcılar", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        # Yeni hatırlatıcı formu
        add_frame = ttk.LabelFrame(content_frame, text="Yeni Hatırlatıcı Ekle", padding="10")
        add_frame.pack(fill=tk.X, pady=5)
        
        fields = ["Başlık", "Açıklama", "Zaman", "Tekrar"]
        entries = {}
        for i, field in enumerate(fields[:3]):
            ttk.Label(add_frame, text=field+":").grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            entries[field] = ttk.Entry(add_frame)
            entries[field].grid(row=i, column=1, padx=5, pady=2)
        
        # Varsayılan değerler
        entries["Zaman"].insert(0, (dt.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(add_frame, text="Tekrar:").grid(row=3, column=0, padx=5, pady=2, sticky=tk.W)
        repeat_var = tk.StringVar(value="yok")
        ttk.Combobox(add_frame, textvariable=repeat_var, values=["yok", "günlük", "haftalık"]).grid(row=3, column=1, padx=5, pady=2)
        
        ttk.Button(add_frame, text="Ekle", command=lambda: self.add_reminder(
            entries["Başlık"].get(),
            entries["Açıklama"].get(),
            entries["Zaman"].get(),
            repeat_var.get()
        )).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Hatırlatıcı listesi
        list_frame = ttk.LabelFrame(content_frame, text="Hatırlatıcı Listesi", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tree = ttk.Treeview(list_frame, columns=("Başlık", "Açıklama", "Zaman", "Tekrar"), show="headings")
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill=tk.BOTH, expand=True)
        
        for rem in self.get_reminders():
            time = dt.strptime(rem['reminder_time'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
            tree.insert("", tk.END, values=(
                rem['title'],
                rem['description'] or "-",
                time,
                rem['repeat_interval'] or "-"
            ))

    def show_profile(self):
        self.clear_main_frame()
        self.create_menu_frame()
        
        content_frame = ttk.Frame(self.main_frame, padding="15 10 15 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Profil Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=5)
        
        # Profil formu
        form_frame = ttk.Frame(content_frame, padding="10")
        form_frame.pack(fill=tk.X, pady=5)
        
        fields = ["Tam Ad", "Email", "Telefon", "Adres", "Acil Durum"]
        entries = {}
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=field+":").grid(row=i, column=0, padx=5, pady=2, sticky=tk.W)
            entries[field] = ttk.Entry(form_frame)
            entries[field].grid(row=i, column=1, padx=5, pady=2)
        
        # Mevcut bilgileri yükle
        entries["Tam Ad"].insert(0, self.current_user['full_name'] or "")
        entries["Email"].insert(0, self.current_user['email'] or "")
        entries["Telefon"].insert(0, self.current_user['phone'] or "")
        entries["Adres"].insert(0, self.current_user['address'] or "")
        entries["Acil Durum"].insert(0, self.current_user['emergency_contact'] or "")
        
        ttk.Button(form_frame, text="Kaydet", command=lambda: self.update_profile(
            entries["Tam Ad"].get(),
            entries["Email"].get(),
            entries["Telefon"].get(),
            entries["Adres"].get(),
            entries["Acil Durum"].get()
        )).grid(row=len(fields), column=0, columnspan=2, pady=5)

    def create_menu_frame(self):
        menu_frame = ttk.Frame(self.main_frame, width=150, relief=tk.RIDGE, padding="10 5 10 5")
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(menu_frame, text=f"Hoş geldiniz,\n{self.current_user['full_name']}", 
                 font=('Helvetica', 10, 'bold')).pack(pady=10)
        
        buttons = [
            ("Ana Sayfa", self.show_elder_dashboard),
            ("Sağlık Bilgileri", self.show_health_info),
            ("İlaçlarım", self.show_medications),
            ("Hatırlatıcılar", self.show_reminders),
            ("Profil", self.show_profile),
            ("Çıkış Yap", self.logout)
        ]
        
        for text, cmd in buttons:
            ttk.Button(menu_frame, text=text, command=cmd, width=15).pack(pady=3)

    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # Veritabanı işlemleri
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Hata", "Kullanıcı adı ve şifre gereklidir")
            return
        
        cursor = self.db_connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user and self.check_password(password, user[2]):
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'full_name': user[3],
                'email': user[4],
                'phone': user[5],
                'role': user[6],
                'address': user[7],
                'emergency_contact': user[8]
            }
            self.show_elder_dashboard()
        else:
            messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre")

    def register(self, username, password, confirm_password, full_name, email, phone, role):
        if not username or not password:
            messagebox.showerror("Hata", "Kullanıcı adı ve şifre gereklidir")
            return
        
        if password != confirm_password:
            messagebox.showerror("Hata", "Şifreler eşleşmiyor")
            return
        
        cursor = self.db_connection.cursor()
        
        # Kullanıcı adı kontrolü
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            messagebox.showerror("Hata", "Bu kullanıcı adı zaten alınmış")
            return
        
        # Kullanıcıyı kaydet
        hashed_password = self.hash_password(password)
        cursor.execute('''
        INSERT INTO users (username, password, full_name, email, phone, role)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, full_name, email, phone, role))
        
        self.db_connection.commit()
        messagebox.showinfo("Başarılı", "Kayıt başarılı. Giriş yapabilirsiniz.")
        self.show_login_screen()

    def add_health_data(self, blood_pressure, heart_rate, blood_sugar, weight, notes):
        if not any([blood_pressure, heart_rate, blood_sugar, weight]):
            messagebox.showerror("Hata", "En az bir alan doldurulmalıdır")
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute('''
            INSERT INTO health_data (user_id, blood_pressure, heart_rate, blood_sugar, weight, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.current_user['id'], 
                 blood_pressure if blood_pressure else None,
                 int(heart_rate) if heart_rate else None,
                 float(blood_sugar) if blood_sugar else None,
                 float(weight) if weight else None,
                 notes if notes else None))
            
            self.db_connection.commit()
            messagebox.showinfo("Başarılı", "Sağlık verileri kaydedildi")
            self.show_health_info()
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz veri formatı")

    def add_medication(self, name, dosage, frequency, start_date, end_date, instructions):
        if not name:
            messagebox.showerror("Hata", "İlaç adı gereklidir")
            return
        
        try:
            # Tarih formatı kontrolü
            dt.strptime(start_date, "%Y-%m-%d %H:%M")
            dt.strptime(end_date, "%Y-%m-%d %H:%M")
            
            cursor = self.db_connection.cursor()
            cursor.execute('''
            INSERT INTO medications (user_id, name, dosage, frequency, start_date, end_date, instructions)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.current_user['id'], name, dosage, frequency, start_date, end_date, instructions))
            
            self.db_connection.commit()
            messagebox.showinfo("Başarılı", "İlaç bilgileri kaydedildi")
            self.show_medications()
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz tarih formatı (YYYY-MM-DD HH:MM)")

    def add_reminder(self, title, description, reminder_time, repeat_interval):
        if not title or not reminder_time:
            messagebox.showerror("Hata", "Başlık ve zaman gereklidir")
            return
        
        try:
            # Zaman formatı kontrolü ve düzeltme
            reminder_time = dt.strptime(reminder_time, "%Y-%m-%d %H:%M").strftime("%Y-%m-%d %H:%M:%S")
            
            cursor = self.db_connection.cursor()
            cursor.execute('''
            INSERT INTO reminders (user_id, title, description, reminder_time, repeat_interval)
            VALUES (?, ?, ?, ?, ?)
            ''', (self.current_user['id'], title, description, reminder_time, repeat_interval))
            
            self.db_connection.commit()
            messagebox.showinfo("Başarılı", "Hatırlatıcı eklendi")
            
            # Hatırlatıcıyı zamanla
            self.schedule_reminder(title, description, reminder_time, repeat_interval)
            self.show_reminders()
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz zaman formatı (YYYY-MM-DD HH:MM)")

    def update_profile(self, full_name, email, phone, address, emergency_contact):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        UPDATE users SET 
            full_name = ?,
            email = ?,
            phone = ?,
            address = ?,
            emergency_contact = ?
        WHERE id = ?
        ''', (full_name, email, phone, address, emergency_contact, self.current_user['id']))
        
        self.db_connection.commit()
        messagebox.showinfo("Başarılı", "Profil güncellendi")
        
        # Kullanıcı bilgilerini yenile
        self.current_user.update({
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'address': address,
            'emergency_contact': emergency_contact
        })

    # Yardımcı fonksiyonlar
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password, hashed_password):
        return self.hash_password(password) == hashed_password
    
    def get_latest_health_data(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM health_data 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
        ''', (self.current_user['id'],))
        
        columns = [column[0] for column in cursor.description]
        data = cursor.fetchone()
        return dict(zip(columns, data)) if data else None
    
    def get_health_history(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM health_data 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
        ''', (self.current_user['id'],))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_active_medications(self):
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM medications 
        WHERE user_id = ? 
        AND start_date <= ?
        AND end_date >= ?
        ORDER BY name
        ''', (self.current_user['id'], now, now))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_medications(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM medications 
        WHERE user_id = ? 
        ORDER BY start_date DESC
        ''', (self.current_user['id'],))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_upcoming_reminders(self):
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM reminders 
        WHERE user_id = ? 
        AND reminder_time >= ?
        AND is_completed = 0
        ORDER BY reminder_time
        LIMIT 5
        ''', (self.current_user['id'], now))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_reminders(self):
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM reminders 
        WHERE user_id = ? 
        ORDER BY reminder_time DESC
        ''', (self.current_user['id'],))
        
        columns = [column[0] for column in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def schedule_reminder(self, title, description, reminder_time_str, repeat_interval):
        try:
            reminder_time = dt.strptime(reminder_time_str, "%Y-%m-%d %H:%M:%S")
            now = dt.now()
            delay = (reminder_time - now).total_seconds()
            
            if delay > 0:
                timer = Timer(delay, self.show_reminder_notification, 
                             args=(title, description, repeat_interval, reminder_time_str))
                timer.start()
                self.reminder_timers.append(timer)
        except ValueError:
            pass
    
    def show_reminder_notification(self, title, description, repeat_interval, original_time_str):
        message = f"{title}\n{description}" if description else title
        messagebox.showinfo("Hatırlatıcı", message)
        
        # Tekrarlanan hatırlatıcıları yeniden zamanla
        if repeat_interval == "günlük":
            next_time = dt.strptime(original_time_str, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1)
            self.add_reminder(title, description, next_time.strftime("%Y-%m-%d %H:%M"), repeat_interval)
        elif repeat_interval == "haftalık":
            next_time = dt.strptime(original_time_str, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(weeks=1)
            self.add_reminder(title, description, next_time.strftime("%Y-%m-%d %H:%M"), repeat_interval)
    
    def load_reminders(self):
        if not self.current_user:
            return
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
        SELECT * FROM reminders 
        WHERE user_id = ? 
        AND is_completed = 0
        AND reminder_time > datetime('now')
        ''', (self.current_user['id'],))
        
        columns = [column[0] for column in cursor.description]
        reminders = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        for reminder in reminders:
            self.schedule_reminder(
                reminder['title'],
                reminder['description'],
                reminder['reminder_time'],
                reminder['repeat_interval']
            )
    
    def logout(self):
        for timer in self.reminder_timers:
            timer.cancel()
        self.reminder_timers.clear()
        self.current_user = None
        self.show_login_screen()
    
    def __del__(self):
        for timer in self.reminder_timers:
            timer.cancel()
        if hasattr(self, 'db_connection'):
            self.db_connection.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ElderCareApp(root)
    root.mainloop()