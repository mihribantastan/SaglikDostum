from flask import Blueprint, render_template, request, session, jsonify
import sqlite3
import hashlib
import difflib
import random
import re
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

chatbot_bp = Blueprint('chatbot', __name__)

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

def get_user_data(user_id):
    row = query_db('SELECT * FROM users WHERE id = ?', [user_id], one=True)
    return dict(row) if row else None

def get_last_health_data(user_id):
    return query_db('SELECT * FROM health_data WHERE user_id=? ORDER BY timestamp DESC LIMIT 1', [user_id], one=True)

def get_health_history(user_id, limit=5):
    return query_db('SELECT * FROM health_data WHERE user_id=? ORDER BY timestamp DESC LIMIT ?', [user_id, limit])

def get_active_medications(user_id):
    return query_db('SELECT * FROM medications WHERE user_id=? AND (end_date IS NULL OR end_date >= datetime("now"))', [user_id])

def get_upcoming_reminders(user_id, limit=3):
    return query_db('''SELECT * FROM reminders 
                      WHERE user_id=? AND reminder_time >= datetime('now') 
                      AND (is_completed = 0 OR is_completed IS NULL) 
                      ORDER BY reminder_time ASC LIMIT ?''', [user_id, limit])

def get_reminder_by_title(user_id, title):
    return query_db('SELECT * FROM reminders WHERE user_id=? AND title LIKE ?', [user_id, f"%{title}%"], one=True)

def delete_reminder(user_id, title):
    execute_db('DELETE FROM reminders WHERE user_id=? AND title LIKE ?', [user_id, f"%{title}%"])

def get_motivation():
    motivs = [
        "Her yeni gün sağlığınız için bir fırsattır.",
        "Küçük adımlar büyük farklar yaratır.",
        "Sağlığınızı önceliklendirdiğiniz için tebrikler!",
        "Kendinize iyi bakmanız için buradayım.",
        "Unutmayın: Düzenli takip, sağlıklı yaşam demektir!",
    ]
    return random.choice(motivs)

def jaccard_similarity(a, b):
    set1 = set(a.split())
    set2 = set(b.split())
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / (union + 1e-6)

def cosine_sim(text1, text2, vectorizer=None):
    if not vectorizer:
        vectorizer = TfidfVectorizer().fit([text1, text2])
    vectors = vectorizer.transform([text1, text2])
    return cosine_similarity(vectors[0], vectors[1])[0][0]

def normalized_levenshtein(s1, s2):
    distance = levenshtein_distance(s1, s2)
    max_len = max(len(s1), len(s2))
    return 1 - (distance / max_len) if max_len != 0 else 1.0

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def sentence_match(message, patterns, threshold=0.65):
    message = message.lower().strip()
    best_score = 0
    
    for pat in patterns:
        pat_low = pat.lower()
        jaccard = jaccard_similarity(message, pat_low)
        cosine = cosine_sim(message, pat_low)
        leven = normalized_levenshtein(message, pat_low)
        avg_score = (jaccard + cosine + leven) / 3
        
        if avg_score > best_score:
            best_score = avg_score
            
    return best_score >= threshold

def extract_entities(text):
    entities = {
        "DATE": [],
        "TIME": [],
        "MEDICINE": [],
        "ACTION": [],
        "QUANTITY": []
    }
    
    words = text.lower().split()
    time_words = ['yarın', 'bugün', 'haftaya', 'gelecek hafta', 'ay', 'gün', 'hafta', 'saat', 'dakika']
    for word in words:
        if word in time_words:
            entities["DATE"].append(word)
        elif re.match(r'\d{1,2}:\d{2}', word):
            entities["TIME"].append(word)
        elif re.match(r'\d+[.]?\d*', word):
            entities["QUANTITY"].append(word)
    
    medicine_keywords = ['hap', 'tablet', 'şurup', 'ilaç', 'kapsül', 'damla']
    for i, word in enumerate(words):
        if word in medicine_keywords and i > 0:
            entities["MEDICINE"].append(words[i-1] + ' ' + word)
    
    action_words = ['al', 'iç', 'kullan', 'sil', 'ekle', 'değiştir', 'göster', 'söyle']
    for word in words:
        if word in action_words:
            entities["ACTION"].append(word)
    
    return entities

def extract_reminder_title(msg):
    patterns = [
        r'(?:sil|kaldır|iptal et)\s+(.+)',
        r'(.+?) hatırlatıcısını sil',
        r'(.+?) alarmını kapat',
        r'(.+?) için hatırlatmayı durdur'
    ]
    
    for pattern in patterns:
        m = re.search(pattern, msg, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    
    return None

def find_closest_match(user_input, options):
    matches = difflib.get_close_matches(user_input.lower(), options, n=1, cutoff=0.6)
    return matches[0] if matches else None

def suggest_alternative(user_input):
    all_options = []
    for kb_item in KNOWLEDGE_BASE.values():
        all_options.extend(kb_item["patterns"])
    
    closest = find_closest_match(user_input, all_options)
    if closest:
        return f"Sanırım şunu sormak istediniz: '{closest}'? Eğer öyleyse tekrar yazın."
    return None

RESPONSE_TEMPLATES = {
    "greeting": [
        "Merhaba {name}! Size nasıl yardımcı olabilirim?",
        "Selam {name}! Bugün nasılsınız?",
        "Hoş geldiniz {name}! Sizin için ne yapabilirim?"
    ],
    "thanks": [
        "Rica ederim, her zaman yardımcı olmaktan mutluluk duyarım!",
        "Ne demek, ben teşekkür ederim!",
        "Benim için bir zevk!"
    ],
    "farewell": [
        "Görüşmek üzere! Sağlıklı günler dilerim.",
        "Hoşça kalın! İyi günler.",
        "Güle güle! Sorularınız olursa buradayım."
    ],
    "unknown": [
        "Üzgünüm, sorunuzu tam olarak anlayamadım. Daha açık yazar mısınız?",
        "Bu konuda yardımcı olamayacağım için üzgünüm. Başka bir şey sorabilir misiniz?",
        "Sanırım yanlış anlaşılma oldu. Lütfen sorunuzu farklı şekilde ifade edin."
    ]
}

KNOWLEDGE_BASE = {
    "app_info": {
        "patterns": [
            'bu uygulama ne işe yarar',
            'uygulamayı nasıl kullanırım',
            'neler yapabilirim',
            'özellikler nelerdir',
            'yardım',
            'uygulama hakkında bilgi'
        ],
        "response": (
            "Bu uygulamada sağlık ölçümlerinizi kaydedebilir, ilaç ve hatırlatıcılarınızı yönetebilir, "
            "profil bilgilerinizi güncelleyebilirsiniz. Ayrıca geçmiş sağlık verilerinizi görebilir, "
            "düzenli takibinizi sağlayabilirsiniz. Detaylar veya örnek sorular için 'örnek' yazabilirsiniz."
        )
    },
    "profile_info": {
        "patterns": [
            'profilim',
            'bilgilerim',
            'adım ne',
            'ismim ne',
            'emailim nedir',
            'telefonum nedir',
            'kullanıcı adım',
            'profilimi göster',
            'kişisel bilgilerim',
            'ben kimim'
        ],
        "response_func": lambda user: (
            f"Adınız: {user.get('full_name','')}\n"
            f"Kullanıcı adınız: {user.get('username','')}\n"
            f"E-posta: {user.get('email','') or 'Yok'}\n"
            f"Telefon: {user.get('phone','') or 'Yok'}"
        )
    },
    "health_measure": {
        "patterns": [
            'nasıl ölçüm yapabilirim',
            'ölçüm nasıl eklerim',
            'sağlık verisi nasıl kaydederim',
            'kan basıncı nasıl eklerim',
            'tansiyonumu nasıl kaydederim'
        ],
        "response": (
            "Sağlık ölçümlerinizi eklemek için:\n"
            "1. Ana menüden 'Sağlık Ölçümleri'ne gidin\n"
            "2. 'Yeni Ölçüm Ekle' butonuna tıklayın\n"
            "3. İlgili alanları doldurun (tansiyon, nabız, kan şekeri vb.)\n"
            "4. 'Kaydet' butonuna basın\n"
            "Ölçümleriniz otomatik olarak kaydedilecek ve geçmişinizde görünecektir."
        )
    },
    "medication_add": {
        "patterns": [
            'ilaç nasıl eklerim',
            'yeni ilaç kaydet',
            'kullandığım ilacı nasıl eklerim',
            'ilaç ekleme nasıl yapılır'
        ],
        "response": (
            "İlaç eklemek için:\n"
            "1. Ana menüden 'İlaçlarım' bölümüne gidin\n"
            "2. 'Yeni İlaç Ekle' butonuna tıklayın\n"
            "3. İlaç adı, dozaj, başlangıç tarihi ve kullanım sıklığını girin\n"
            "4. Gerekirse bitiş tarihi ekleyin\n"
            "5. 'Kaydet' butonuna basın\n"
            "Eklediğiniz ilaçlar hatırlatıcı olarak ayarlanabilir."
        )
    },
    "reminder_add": {
        "patterns": [
            'hatırlatıcı nasıl eklerim',
            'yeni hatırlatıcı oluştur',
            'alarm nasıl kurarım',
            'hatırlatma nasıl ayarlarım'
        ],
        "response": (
            "Hatırlatıcı eklemek için:\n"
            "1. Ana menüden 'Hatırlatıcılar' bölümüne gidin\n"
            "2. 'Yeni Hatırlatıcı Ekle' butonuna tıklayın\n"
            "3. Hatırlatıcı başlığı ve zamanını girin\n"
            "4. İsteğe bağlı tekrarlama ayarlarını yapın\n"
            "5. 'Kaydet' butonuna basın\n"
            "Hatırlatıcılarınız belirlediğiniz zamanda size bildirim olarak gelecektir."
        )
    },
    "example_questions": {
        "patterns": [
            'örnek sorular',
            'neyi sorabilirim',
            'hangi soruları sorabilirim',
            'örnek göster',
            'neler sorabilirim'
        ],
        "response": (
            "Bana şu tür sorular sorabilirsiniz:\n"
            "- Son sağlık ölçümüm ne?\n"
            "- Aktif ilaçlarım neler?\n"
            "- Yaklaşan hatırlatıcılarım var mı?\n"
            "- Sabah ilacı hatırlatıcısını sil\n"
            "- Profil bilgilerimi göster\n"
            "- Uygulama hakkında bilgi ver\n"
            "- Beni motive et\n"
            "Sağlık, ilaç, hatırlatıcı ve profil bilgilerinizle ilgili sorular sorabilirsiniz."
        )
    },
    "reminders": {
        "patterns": [
            'hatırlatıcılarım',
            'hatırlatmalarım',
            'alarmlarım',
            'yaklaşan hatırlatıcılar',
            'planlarım'
        ],
        "response_func": lambda user: get_reminders_response(user['id'])
    },
    "medications": {
        "patterns": [
            'ilaçlarım',
            'aktif ilaçlarım',
            'hangi ilaçları kullanıyorum',
            'ilacım var mı',
            'kullandığım ilaçlar'
        ],
        "response_func": lambda user: get_medications_response(user['id'])
    }
}

def get_reminders_response(user_id):
    reminders = get_upcoming_reminders(user_id)
    if reminders:
        response = "Yaklaşan hatırlatıcılarınız:\n"
        for r in reminders:
            response += f"- {r['title']} ({r['reminder_time']})\n"
        return response
    return "Yaklaşan bir hatırlatıcınız yok."

def get_medications_response(user_id):
    meds = get_active_medications(user_id)
    if meds:
        response = "Şu an kullandığınız ilaçlar:\n"
        for m in meds:
            m = dict(m)  
            response += f"- {m['name']} ({m['dosage']}) {m.get('frequency','')} [Başlangıç: {m['start_date']}]"
            if m.get('end_date'): 
                response += f" Bitiş: {m['end_date']}"
            response += "\n"
        return response
    return "Kayıtlı aktif ilacınız bulunmuyor."

class AdvancedChatbot:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user_data = get_user_data(user_id)
        self.context = {}
        self.vectorizer = TfidfVectorizer()
    
    def get_response(self, message):
        if not self.user_data:
            return "Kullanıcı bulunamadı. Lütfen giriş yapın."
        
        msg = message.lower().strip()
        
        # Konuşma akışını kontrol et
        flow_response = self.handle_conversation_flow(message)
        if flow_response:
            return flow_response
        
        personal_response = self.handle_personal_questions(message)
        if personal_response:
            return personal_response
        
        entities = extract_entities(message)
        self.update_context(message, entities)
        
        response = self.determine_response(msg, entities)
        
        return response
    
    def handle_conversation_flow(self, message):
        msg = message.lower().strip()
        
        if msg in ['iyiyim', 'iyi', 'teşekkürler']:
            return random.choice([
                "Harika duydum! Size nasıl yardımcı olabilirim?",
                "Bu güzel bir haber! Başka bir isteğiniz var mı?",
                "Güzel! Sizin için başka ne yapabilirim?"
            ])
        
        if msg in ['ben', 'ben?']:
            return ("Profil bilgilerinizi mi öğrenmek istiyorsunuz? "
                    "'Profilim' yazarsanız bilgilerinizi gösterebilirim.")
        
        return None
    
    def handle_personal_questions(self, message):
        personal_keywords = {
            'ben kimim': 'profilim',
            'kimim': 'profilim',
            'adım ne': 'profilim',
            'verilerim': 'sağlık geçmişim',
            'bilgilerim': 'profilim',
            'saat': lambda: f"Şu an saat: {datetime.now().strftime('%H:%M')}"
        }
        
        msg = message.lower().strip()
        for keyword, response in personal_keywords.items():
            if keyword in msg:
                if callable(response):
                    return response()
                return self.get_response(response)
        return None
    
    def update_context(self, message, entities):
        if entities.get("DATE") or entities.get("TIME"):
            self.context["time_reference"] = entities.get("DATE", []) + entities.get("TIME", [])
        
        if entities.get("MEDICINE"):
            self.context["medicine"] = entities["MEDICINE"][0]
        
        if entities.get("ACTION"):
            self.context["action"] = entities["ACTION"][0]
    
    def determine_response(self, message, entities):
        special_case = self.check_special_cases(message)
        if special_case:
            return self.handle_special_cases(special_case)
        
        kb_match = self.match_knowledge_base(message)
        if kb_match:
            return kb_match
        
        db_response = self.generate_db_based_response(message, entities)
        if db_response:
            return db_response
        
        suggestion = suggest_alternative(message)
        if suggestion:
            return suggestion
        
        return self.get_template_response("unknown")
    
    def check_special_cases(self, message):
        if sentence_match(message, ['merhaba', 'selam', 'günaydın', 'iyi akşamlar', 'iyi geceler', 'hey', 'selamlar']):
            return "greeting"
        
        if sentence_match(message, ['teşekkür', 'sağ ol', 'eyvallah', 'minnettarım', 'teşekkür ederim', 'çok teşekkür']):
            return "thanks"
        
        if sentence_match(message, ['görüşürüz', 'hoşça kal', 'bye', 'çıkış yap', 'kendine iyi bak', 'güle güle']):
            return "farewell"
        
        return None
    
    def handle_special_cases(self, case_type):
        templates = RESPONSE_TEMPLATES.get(case_type, [])
        if not templates:
            return ""
        
        if case_type == "greeting":
            return random.choice(templates).format(name=self.user_data.get('full_name', ''))
        else:
            return random.choice(templates)
    
    def match_knowledge_base(self, message):
        for kb_item in KNOWLEDGE_BASE.values():
            if sentence_match(message, kb_item["patterns"]):
                if "response_func" in kb_item:
                    return kb_item["response_func"](self.user_data)
                else:
                    return kb_item["response"]
        return None
    
    def generate_db_based_response(self, message, entities):
        if sentence_match(message, [
            'son sağlık ölçümüm ne', 'en son ölçümüm', 'son sağlık değerim', 
            'en son kaydım', 'son ölçüm'
        ]):
            health = get_last_health_data(self.user_id)
            if health:
                return (
                    f"Son sağlık ölçümünüz ({health['timestamp']}):\n"
                    f"Kan Basıncı: {health['blood_pressure']}\n"
                    f"Nabız: {health['heart_rate']}\n"
                    f"Kan Şekeri: {health['blood_sugar']}\n"
                    f"Kilo: {health['weight']}"
                )
            else:
                return "Henüz bir sağlık ölçümünüz bulunmuyor."
        
        if any(word in message for word in ['hatırlatıcı sil', 'hatırlatıcıyı sil', 'hatırlatıcı kaldır', 'hatırlatıcımı sil']):
            title = extract_reminder_title(message)
            if not title:
                return "Silmek istediğiniz hatırlatıcının adını belirtin. Örn: 'Sabah İlacı hatırlatıcısını sil'"
            reminder = get_reminder_by_title(self.user_id, title)
            if reminder:
                delete_reminder(self.user_id, title)
                return f"'{reminder['title']}' isimli hatırlatıcı silindi."
            else:
                return "Belirttiğiniz isimde bir hatırlatıcı bulunamadı."
        
        if sentence_match(message, ['motivasyon', 'beni motive et', 'cesaret ver', 'motive edici bir şey söyle']):
            return get_motivation()
        
        return None
    
    def get_template_response(self, template_key):
        templates = RESPONSE_TEMPLATES.get(template_key, [])
        if templates:
            return random.choice(templates)
        return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."

# ... (diğer route'lar aynı şekilde devam eder) ...

@chatbot_bp.route('/chatbot', methods=['GET', 'POST'])
def chatbot_route():
    if "user_id" not in session:
        return jsonify({"error": "Önce giriş yapmalısınız."}), 401
    
    user_id = session['user_id']
    
    if request.method == 'POST':
        user_message = request.json.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Boş mesaj gönderilemez."}), 400
        
        bot = AdvancedChatbot(user_id)
        response = bot.get_response(user_message)
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    user = get_user_data(user_id)
    return render_template("chatbot.html", user=user)
