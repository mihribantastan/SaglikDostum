import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from threading import Timer
from datetime import datetime as dt

from database import create_tables
import user_managment
import health_management
import medication_management
import reminder_management

class ElderCareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yaşlı Takip Sistemi")
        self.root.geometry("1000x700")
        self.current_user = None
        self.reminder_timers = []

        # Veritabanı bağlantısı ve tablo oluşturma
        create_tables()

        self.setup_ui()
        self.load_reminders()

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
        health_data = health_management.get_latest_health_data(self.current_user['id'])
        if health_data:
            health_frame = ttk.LabelFrame(content_frame, text="Son Sağlık Ölçümleri", padding="10")
            health_frame.pack(fill=tk.X, pady=5)

            labels = [
                f"Kan Basıncı: {health_data.get('blood_pressure', 'N/A')}",
                f"Nabız: {health_data.get('heart_rate', 'N/A')}",
                f"Kan Şekeri: {health_data.get('blood_sugar', 'N/A')}",
                f"Kilo: {health_data.get('weight', 'N/A')}"
            ]
            for label in labels:
                ttk.Label(health_frame, text=label).pack(anchor=tk.W)

        # Yaklaşan hatırlatıcılar
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        reminders = reminder_management.get_upcoming_reminders(self.current_user['id'], now)
        if reminders:
            rem_frame = ttk.LabelFrame(content_frame, text="Yaklaşan Hatırlatıcılar", padding="10")
            rem_frame.pack(fill=tk.X, pady=5)

            for rem in reminders[:3]:  # En fazla 3 hatırlatıcı göster
                time = dt.strptime(rem['reminder_time'], '%Y-%m-%d %H:%M:%S').strftime('%d.%m %H:%M')
                ttk.Label(rem_frame, text=f"{rem['title']} - {time}").pack(anchor=tk.W)

        # Aktif ilaçlar
        meds = medication_management.get_active_medications(self.current_user['id'], now)
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

        for data in health_management.get_health_history(self.current_user['id']):
            tree.insert("", tk.END, values=(
                data['timestamp'][:16],
                data.get('blood_pressure', "-"),
                data.get('heart_rate', "-"),
                data.get('blood_sugar', "-"),
                data.get('weight', "-")
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

        for med in medication_management.get_medications(self.current_user['id']):
            tree.insert("", tk.END, values=(
                med['name'],
                med.get('dosage', "-"),
                med.get('frequency', "-"),
                med['start_date'][:16],
                med['end_date'][:16]
            ))

def add_medication(self, name, dosage, frequency, start_time, end_time, instructions):
    if not name or not dosage:
        messagebox.showerror("Hata", "İlaç adı ve dozaj boş olamaz.")
        return

    medication_management.add_medication(
        self.current_user['id'], name, dosage, frequency,
        start_time, end_time, instructions
    )
    messagebox.showinfo("Başarılı", "İlaç eklendi.")
    self.show_medications()
