import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import json
from threading import Timer
import os
import sys
import hashlib
from PIL import Image, ImageTk

class ElderCareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yaşlı Takip Sistemi")
        self.root.geometry("1200x800")
        self.current_user = None
        self.reminder_timers = []
        
        # Veritabanı bağlantısı
        self.db_connection = sqlite3.connect('eldercare.db')
        self.create_tables()
        
        # Arayüz bileşenleri
        self.setup_ui()
        
        # Hatırlatıcıları yükle
        self.load_reminders()
        
    def create_tables(self):
        cursor = self.db_connection.cursor()
        
        # Kullanıcılar tablosu - yorum satırı düzeltildi
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            role TEXT NOT NULL,  -- elder, relative, admin
            address TEXT,
            emergency_contact TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Aile ilişkileri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS family_relations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            elder_id INTEGER NOT NULL,
            relative_id INTEGER NOT NULL,
            relation_type TEXT,
            confirmed BOOLEAN DEFAULT 0,
            FOREIGN KEY (elder_id) REFERENCES users(id),
            FOREIGN KEY (relative_id) REFERENCES users(id)
        )
        ''')
        
        # Sağlık verileri tablosu
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
        )
        ''')
        
        # İlaçlar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            instructions TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Hatırlatıcılar tablosu - yorum satırı düzeltildi
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            reminder_time TIMESTAMP NOT NULL,
            repeat_interval TEXT,  -- daily, weekly, none
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        self.db_connection.commit()

    
    def setup_ui(self):
        # Ana çerçeve
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Giriş ekranı
        self.show_login_screen()
    
    def show_login_screen(self):
        self.clear_main_frame()
        
        login_frame = ttk.Frame(self.main_frame, padding="30 15 30 15")
        login_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(login_frame, text="Kullanıcı Adı:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Şifre:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        login_btn = ttk.Button(login_frame, text="Giriş Yap", command=self.login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        register_btn = ttk.Button(login_frame, text="Kayıt Ol", command=self.show_register_screen)
        register_btn.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Varsayılan değerler (geliştirme için)
        self.username_entry.insert(0, "elder1")
        self.password_entry.insert(0, "password123")
    
    def show_register_screen(self):
        self.clear_main_frame()
        
        register_frame = ttk.Frame(self.main_frame, padding="30 15 30 15")
        register_frame.pack(fill=tk.BOTH, expand=True)
        
        # Kullanıcı bilgileri
        ttk.Label(register_frame, text="Kullanıcı Adı:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        username_entry = ttk.Entry(register_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Şifre:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        password_entry = ttk.Entry(register_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Şifre Tekrar:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        password_confirm_entry = ttk.Entry(register_frame, show="*")
        password_confirm_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Tam Ad:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        full_name_entry = ttk.Entry(register_frame)
        full_name_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Email:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        email_entry = ttk.Entry(register_frame)
        email_entry.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Telefon:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        phone_entry = ttk.Entry(register_frame)
        phone_entry.grid(row=5, column=1, padx=5, pady=5)
        
        ttk.Label(register_frame, text="Rol:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        role_var = tk.StringVar(value="elder")
        role_combobox = ttk.Combobox(register_frame, textvariable=role_var, values=["elder", "relative"])
        role_combobox.grid(row=6, column=1, padx=5, pady=5)
        
        register_btn = ttk.Button(register_frame, text="Kayıt Ol", command=lambda: self.register(
            username_entry.get(),
            password_entry.get(),
            password_confirm_entry.get(),
            full_name_entry.get(),
            email_entry.get(),
            phone_entry.get(),
            role_var.get()
        ))
        register_btn.grid(row=7, column=0, columnspan=2, pady=10)
        
        back_btn = ttk.Button(register_frame, text="Geri", command=self.show_login_screen)
        back_btn.grid(row=8, column=0, columnspan=2, pady=5)
    
    def show_elder_dashboard(self):
        self.clear_main_frame()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sol panel (menü)
        menu_frame = ttk.Frame(main_frame, width=200, relief=tk.RIDGE, padding="10 5 10 5")
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(menu_frame, text=f"Hoş geldiniz,\n{self.current_user['full_name']}", 
                 font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        menu_buttons = [
            ("Sağlık Bilgileri", self.show_health_info),
            ("İlaçlarım", self.show_medications),
            ("Hatırlatıcılar", self.show_reminders),
            ("Profil", self.show_profile),
            ("Çıkış Yap", self.logout)
        ]
        
        for text, command in menu_buttons:
            btn = ttk.Button(menu_frame, text=text, command=command, width=20)
            btn.pack(pady=5)
        
        # Sağ panel (içerik)
        content_frame = ttk.Frame(main_frame, padding="20 10 20 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Özet bilgiler
        ttk.Label(content_frame, text="Özet Bilgiler", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Son sağlık verileri
        health_data = self.get_latest_health_data()
        if health_data:
            health_frame = ttk.LabelFrame(content_frame, text="Son Sağlık Ölçümleri", padding="10 5 10 5")
            health_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(health_frame, text=f"Kan Basıncı: {health_data['blood_pressure'] or 'Kayıt Yok'}").pack(anchor=tk.W)
            ttk.Label(health_frame, text=f"Nabız: {health_data['heart_rate'] or 'Kayıt Yok'}").pack(anchor=tk.W)
            ttk.Label(health_frame, text=f"Kan Şekeri: {health_data['blood_sugar'] or 'Kayıt Yok'}").pack(anchor=tk.W)
            ttk.Label(health_frame, text=f"Kilo: {health_data['weight'] or 'Kayıt Yok'}").pack(anchor=tk.W)
        
        # Yaklaşan hatırlatıcılar
        upcoming_reminders = self.get_upcoming_reminders()
        if upcoming_reminders:
            reminders_frame = ttk.LabelFrame(content_frame, text="Yaklaşan Hatırlatıcılar", padding="10 5 10 5")
            reminders_frame.pack(fill=tk.X, pady=5)
            
            for reminder in upcoming_reminders:
                reminder_time = datetime.datetime.strptime(reminder['reminder_time'], '%Y-%m-%d %H:%M:%S')
                reminder_text = f"{reminder['title']} - {reminder_time.strftime('%d.%m.%Y %H:%M')}"
                ttk.Label(reminders_frame, text=reminder_text).pack(anchor=tk.W)
        
        # Aktif ilaçlar
        active_meds = self.get_active_medications()
        if active_meds:
            meds_frame = ttk.LabelFrame(content_frame, text="Aktif İlaçlar", padding="10 5 10 5")
            meds_frame.pack(fill=tk.X, pady=5)
            
            for med in active_meds:
                med_text = f"{med['name']} - {med['dosage']} ({med['frequency']})"
                ttk.Label(meds_frame, text=med_text).pack(anchor=tk.W)
    
    def show_health_info(self):
        self.clear_main_frame()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çerçevesi
        self.create_menu_frame(main_frame)
        
        # İçerik çerçevesi
        content_frame = ttk.Frame(main_frame, padding="20 10 20 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Sağlık Bilgileri", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Yeni ölçüm ekleme formu
        add_frame = ttk.LabelFrame(content_frame, text="Yeni Ölçüm Ekle", padding="10 5 10 5")
        add_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_frame, text="Kan Basıncı (örn: 120/80):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        blood_pressure_entry = ttk.Entry(add_frame)
        blood_pressure_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Nabız:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        heart_rate_entry = ttk.Entry(add_frame)
        heart_rate_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Kan Şekeri (mg/dL):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        blood_sugar_entry = ttk.Entry(add_frame)
        blood_sugar_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Kilo (kg):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        weight_entry = ttk.Entry(add_frame)
        weight_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Notlar:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        notes_entry = ttk.Entry(add_frame)
        notes_entry.grid(row=4, column=1, padx=5, pady=5)
        
        add_btn = ttk.Button(add_frame, text="Kaydet", command=lambda: self.add_health_data(
            blood_pressure_entry.get(),
            heart_rate_entry.get(),
            blood_sugar_entry.get(),
            weight_entry.get(),
            notes_entry.get()
        ))
        add_btn.grid(row=5, column=0, columnspan=2, pady=10)
        
        # Ölçüm geçmişi
        history_frame = ttk.LabelFrame(content_frame, text="Ölçüm Geçmişi", padding="10 5 10 5")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("#1", "#2", "#3", "#4", "#5", "#6")
        tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        
        tree.heading("#1", text="Tarih")
        tree.heading("#2", text="Kan Basıncı")
        tree.heading("#3", text="Nabız")
        tree.heading("#4", text="Kan Şekeri")
        tree.heading("#5", text="Kilo")
        tree.heading("#6", text="Notlar")
        
        tree.column("#1", width=120)
        tree.column("#2", width=100)
        tree.column("#3", width=80)
        tree.column("#4", width=100)
        tree.column("#5", width=80)
        tree.column("#6", width=200)
        
        vsb = ttk.Scrollbar(history_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Verileri yükle
        health_data = self.get_health_history()
        for data in health_data:
            tree.insert("", tk.END, values=(
                data['timestamp'],
                data['blood_pressure'],
                data['heart_rate'],
                data['blood_sugar'],
                data['weight'],
                data['notes']
            ))
    
    def show_medications(self):
        self.clear_main_frame()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çerçevesi
        self.create_menu_frame(main_frame)
        
        # İçerik çerçevesi
        content_frame = ttk.Frame(main_frame, padding="20 10 20 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="İlaçlarım", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Yeni ilaç ekleme formu
        add_frame = ttk.LabelFrame(content_frame, text="Yeni İlaç Ekle", padding="10 5 10 5")
        add_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_frame, text="İlaç Adı:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        name_entry = ttk.Entry(add_frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Dozaj:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        dosage_entry = ttk.Entry(add_frame)
        dosage_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Sıklık:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        frequency_var = tk.StringVar(value="daily")
        frequency_combobox = ttk.Combobox(add_frame, textvariable=frequency_var, 
                                         values=["daily", "bidaily", "tidaily", "weekly"])
        frequency_combobox.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Başlangıç Tarihi:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        start_date_entry = ttk.Entry(add_frame)
        start_date_entry.grid(row=3, column=1, padx=5, pady=5)
        start_date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(add_frame, text="Bitiş Tarihi:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        end_date_entry = ttk.Entry(add_frame)
        end_date_entry.grid(row=4, column=1, padx=5, pady=5)
        end_date_entry.insert(0, (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(add_frame, text="Talimatlar:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        instructions_entry = ttk.Entry(add_frame)
        instructions_entry.grid(row=5, column=1, padx=5, pady=5)
        
        add_btn = ttk.Button(add_frame, text="Ekle", command=lambda: self.add_medication(
            name_entry.get(),
            dosage_entry.get(),
            frequency_var.get(),
            start_date_entry.get(),
            end_date_entry.get(),
            instructions_entry.get()
        ))
        add_btn.grid(row=6, column=0, columnspan=2, pady=10)
        
        # İlaç listesi
        list_frame = ttk.LabelFrame(content_frame, text="İlaç Listesi", padding="10 5 10 5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("#1", "#2", "#3", "#4", "#5", "#6")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        tree.heading("#1", text="İlaç Adı")
        tree.heading("#2", text="Dozaj")
        tree.heading("#3", text="Sıklık")
        tree.heading("#4", text="Başlangıç")
        tree.heading("#5", text="Bitiş")
        tree.heading("#6", text="Talimatlar")
        
        tree.column("#1", width=150)
        tree.column("#2", width=80)
        tree.column("#3", width=80)
        tree.column("#4", width=120)
        tree.column("#5", width=120)
        tree.column("#6", width=200)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Verileri yükle
        medications = self.get_medications()
        for med in medications:
            tree.insert("", tk.END, values=(
                med['name'],
                med['dosage'],
                med['frequency'],
                med['start_date'],
                med['end_date'],
                med['instructions']
            ))
    
    def show_reminders(self):
        self.clear_main_frame()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çerçevesi
        self.create_menu_frame(main_frame)
        
        # İçerik çerçevesi
        content_frame = ttk.Frame(main_frame, padding="20 10 20 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Hatırlatıcılar", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Yeni hatırlatıcı ekleme formu
        add_frame = ttk.LabelFrame(content_frame, text="Yeni Hatırlatıcı Ekle", padding="10 5 10 5")
        add_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_frame, text="Başlık:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        title_entry = ttk.Entry(add_frame)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Açıklama:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        description_entry = ttk.Entry(add_frame)
        description_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(add_frame, text="Zaman:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        time_entry = ttk.Entry(add_frame)
        time_entry.grid(row=2, column=1, padx=5, pady=5)
        time_entry.insert(0, (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"))
        
        ttk.Label(add_frame, text="Tekrar:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        repeat_var = tk.StringVar(value="none")
        repeat_combobox = ttk.Combobox(add_frame, textvariable=repeat_var, 
                                      values=["none", "daily", "weekly"])
        repeat_combobox.grid(row=3, column=1, padx=5, pady=5)
        
        add_btn = ttk.Button(add_frame, text="Ekle", command=lambda: self.add_reminder(
            title_entry.get(),
            description_entry.get(),
            time_entry.get(),
            repeat_var.get()
        ))
        add_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Hatırlatıcı listesi
        list_frame = ttk.LabelFrame(content_frame, text="Hatırlatıcı Listesi", padding="10 5 10 5")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("#1", "#2", "#3", "#4")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        tree.heading("#1", text="Başlık")
        tree.heading("#2", text="Açıklama")
        tree.heading("#3", text="Zaman")
        tree.heading("#4", text="Tekrar")
        
        tree.column("#1", width=150)
        tree.column("#2", width=200)
        tree.column("#3", width=120)
        tree.column("#4", width=80)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Verileri yükle
        reminders = self.get_reminders()
        for reminder in reminders:
            tree.insert("", tk.END, values=(
                reminder['title'],
                reminder['description'],
                reminder['reminder_time'],
                reminder['repeat_interval']
            ))
    
    def show_profile(self):
        self.clear_main_frame()
        
        # Ana çerçeve
        main_frame = ttk.Frame(self.main_frame)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çerçevesi
        self.create_menu_frame(main_frame)
        
        # İçerik çerçevesi
        content_frame = ttk.Frame(main_frame, padding="20 10 20 10")
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        ttk.Label(content_frame, text="Profil Bilgileri", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Profil formu
        form_frame = ttk.Frame(content_frame, padding="10 5 10 5")
        form_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(form_frame, text="Kullanıcı Adı:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        username_label = ttk.Label(form_frame, text=self.current_user['username'])
        username_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(form_frame, text="Tam Ad:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        full_name_entry = ttk.Entry(form_frame)
        full_name_entry.grid(row=1, column=1, padx=5, pady=5)
        full_name_entry.insert(0, self.current_user['full_name'])
        
        ttk.Label(form_frame, text="Email:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        email_entry = ttk.Entry(form_frame)
        email_entry.grid(row=2, column=1, padx=5, pady=5)
        email_entry.insert(0, self.current_user['email'])
        
        ttk.Label(form_frame, text="Telefon:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        phone_entry = ttk.Entry(form_frame)
        phone_entry.grid(row=3, column=1, padx=5, pady=5)
        phone_entry.insert(0, self.current_user['phone'])
        
        ttk.Label(form_frame, text="Adres:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        address_entry = ttk.Entry(form_frame)
        address_entry.grid(row=4, column=1, padx=5, pady=5)
        address_entry.insert(0, self.current_user['address'])
        
        ttk.Label(form_frame, text="Acil Durum İletişim:").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        emergency_entry = ttk.Entry(form_frame)
        emergency_entry.grid(row=5, column=1, padx=5, pady=5)
        emergency_entry.insert(0, self.current_user['emergency_contact'])
        
        save_btn = ttk.Button(form_frame, text="Kaydet", command=lambda: self.update_profile(
            full_name_entry.get(),
            email_entry.get(),
            phone_entry.get(),
            address_entry.get(),
            emergency_entry.get()
        ))
        save_btn.grid(row=6, column=0, columnspan=2, pady=10)
    
    def create_menu_frame(self, parent):
        menu_frame = ttk.Frame(parent, width=200, relief=tk.RIDGE, padding="10 5 10 5")
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(menu_frame, text=f"Hoş geldiniz,\n{self.current_user['full_name']}", 
                 font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        menu_buttons = [
            ("Ana Sayfa", self.show_elder_dashboard),
            ("Sağlık Bilgileri", self.show_health_info),
            ("İlaçlarım", self.show_medications),
            ("Hatırlatıcılar", self.show_reminders),
            ("Profil", self.show_profile),
            ("Çıkış Yap", self.logout)
        ]
        
        for text, command in menu_buttons:
            btn = ttk.Button(menu_frame, text=text, command=command, width=20)
            btn.pack(pady=5)
    
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
        
        # Email kontrolü
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                messagebox.showerror("Hata", "Bu email zaten kayıtlı")
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
        if not any([blood_pressure, heart_rate, blood_sugar, weight, notes]):
            messagebox.showerror("Hata", "En az bir alan doldurulmalıdır")
            return
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
        INSERT INTO health_data (user_id, blood_pressure, heart_rate, blood_sugar, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.current_user['id'], blood_pressure, heart_rate, blood_sugar, weight, notes))
        
        self.db_connection.commit()
        messagebox.showinfo("Başarılı", "Sağlık verileri kaydedildi")
        self.show_health_info()
    
    def add_medication(self, name, dosage, frequency, start_date, end_date, instructions):
        if not name:
            messagebox.showerror("Hata", "İlaç adı gereklidir")
            return
        
        try:
            start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M")
            end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz tarih formatı (YYYY-MM-DD HH:MM)")
            return
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
        INSERT INTO medications (user_id, name, dosage, frequency, start_date, end_date, instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (self.current_user['id'], name, dosage, frequency, start_date, end_date, instructions))
        
        self.db_connection.commit()
        messagebox.showinfo("Başarılı", "İlaç bilgileri kaydedildi")
        
        # İlaç için hatırlatıcı oluştur
        self.create_medication_reminders(name, dosage, frequency, start_datetime, end_datetime)
        
        self.show_medications()
    
    def add_reminder(self, title, reminder_time, repeat_interval, description=""):
        if not title or not reminder_time:
            messagebox.showerror("Hata", "Başlık ve zaman gereklidir")
            return
        
        try:
            datetime.datetime.strptime(reminder_time, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz zaman formatı (YYYY-MM-DD HH:MM)")
            return
        
        cursor = self.db_connection.cursor()
        cursor.execute('''
        INSERT INTO reminders (user_id, title, description, reminder_time, repeat_interval)
        VALUES (?, ?, ?, ?, ?)
        ''', (self.current_user['id'], title, description, reminder_time, repeat_interval))
        
        self.db_connection.commit()
        messagebox.showinfo("Başarılı", "Hatırlatıcı eklendi")
        
        # Hatırlatıcıyı zamanlayıcıya ekle
        self.schedule_reminder(title, description, reminder_time, repeat_interval)
        
        self.show_reminders()
    
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
        
        self.show_profile()
    
    # Yardımcı fonksiyonlar
    def hash_password(self, password):
        """Basit bir şifre hashleme fonksiyonu"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def check_password(self, password, hashed_password):
        """Şifre kontrolü"""
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
        
        if data:
            return dict(zip(columns, data))
        return None
    
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
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
    
    def create_medication_reminders(self, name, dosage, frequency, start_datetime, end_datetime):
        """İlaç için otomatik hatırlatıcılar oluşturur"""
        if frequency == "daily":
            interval = datetime.timedelta(days=1)
        elif frequency == "bidaily":
            interval = datetime.timedelta(hours=12)
        elif frequency == "tidaily":
            interval = datetime.timedelta(hours=8)
        elif frequency == "weekly":
            interval = datetime.timedelta(weeks=1)
        else:
            return
        
        current_time = start_datetime
        while current_time <= end_datetime:
            title = f"İlaç Zamanı: {name}"
            description = f"{dosage} almayı unutmayın"
            
            self.add_reminder(
                title=title,
                description=description,
                reminder_time=current_time.strftime("%Y-%m-%d %H:%M"),
                repeat_interval="none"
            )
            
            current_time += interval
    
    def schedule_reminder(self, title, description, reminder_time_str, repeat_interval):
        """Hatırlatıcıyı zamanlar"""
        try:
            reminder_time = datetime.datetime.strptime(reminder_time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            return
        
        now = datetime.datetime.now()
        delay = (reminder_time - now).total_seconds()
        
        if delay > 0:
            timer = Timer(delay, self.show_reminder_notification, args=(title, description, repeat_interval, reminder_time_str))
            timer.start()
            self.reminder_timers.append(timer)
    
    def show_reminder_notification(self, title, description, repeat_interval, original_time_str):
        """Hatırlatıcı bildirimi gösterir"""
        message = f"{title}\n\n{description}" if description else title
        messagebox.showinfo("Hatırlatıcı", message)
        
        # Tekrarlanan hatırlatıcıları yeniden zamanla
        if repeat_interval == "daily":
            next_time = datetime.datetime.strptime(original_time_str, "%Y-%m-%d %H:%M") + datetime.timedelta(days=1)
            self.add_reminder(title, description, next_time.strftime("%Y-%m-%d %H:%M"), repeat_interval)
        elif repeat_interval == "weekly":
            next_time = datetime.datetime.strptime(original_time_str, "%Y-%m-%d %H:%M") + datetime.timedelta(weeks=1)
            self.add_reminder(title, description, next_time.strftime("%Y-%m-%d %H:%M"), repeat_interval)
    
    def load_reminders(self):
        """Kayıtlı hatırlatıcıları yükler ve zamanlar"""
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
        # Zamanlayıcıları temizle
        for timer in self.reminder_timers:
            timer.cancel()
        self.reminder_timers.clear()
        
        self.current_user = None
        self.show_login_screen()
    
    def __del__(self):
        # Zamanlayıcıları temizle
        for timer in self.reminder_timers:
            timer.cancel()
        
        # Veritabanı bağlantısını kapat
        if hasattr(self, 'db_connection'):
            self.db_connection.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = ElderCareApp(root)
    root.mainloop()