# Sağlık Dostum

Sağlık Dostum, yaşlı bireylerin sağlık durumlarını düzenli olarak takip edebilecekleri ve temel sağlık ihtiyaçlarını dijital olarak yönetebilecekleri web tabanlı bir sağlık takip sistemidir.

## İçindekiler

- [Projenin Hedefleri](#projenin-hedefleri)
- [Projenin Kapsamı](#projenin-kapsamı)
- [Sistem Özellikleri](#sistem-özellikleri)
- [Kurulum](#kurulum)
- [Çalıştırma](#çalıştırma)
- [Dosya ve Klasörler](#dosya-ve-klasörler)
- [Katkıda Bulunma](#katkıda-bulunma)

---

## Projenin Hedefleri

- Yaşlı bireylerin sağlık verilerini kolayca takip etmelerini sağlamak.
- İlaç kullanımını düzenli hale getirmek için hatırlatıcı sistemleri sunmak.
- Kullanıcıların geçmiş sağlık verilerini görüntüleyerek zaman içindeki değişimleri analiz etmelerine yardımcı olmak.
- Basit ve erişilebilir bir arayüz ile teknolojiye aşina olmayan kullanıcıların sistemi rahatça kullanabilmesini sağlamak.
- Toplumsal fayda sağlayarak yaşlı bireylerin yaşam kalitesini artırmak.

## Projenin Kapsamı

- **Kullanıcı Yönetimi:** Kullanıcıların sisteme kaydolması, giriş yapması ve profil bilgilerini güncellemesi.
- **Sağlık Veri Takibi:** Tansiyon, nabız, kan şekeri gibi verilerin günlük olarak kaydedilmesi ve görüntülenmesi.
- **İlaç Yönetimi:** Kullanıcıların ilaç bilgilerini eklemesi, düzenlemesi ve ilaç hatırlatıcıları oluşturması.
- **Hatırlatıcı Sistemi:** İlaç saatleri ve diğer sağlık görevleri için hatırlatıcıların oluşturulması ve yönetilmesi.
- **Sohbet Botu:** Kullanıcıların sağlık verileri hakkında bilgi alması ve temel sorulara yanıt bulması için sohbet botu entegrasyonu.

## Sistem Özellikleri

- Web tabanlı ve sade arayüz
- SQLite veritabanı ile veri saklama
- Flask tabanlı backend mimarisi
- Chatbot entegrasyonu ile bilgilendirici destek
- Kullanıcı dostu ve erişilebilir tasarım
- İlaç hatırlatıcı ve sağlık veri takip sistemleri

## Kurulum

**Gereksinimler**

- Python 3.8+
- pip

**Gerekli Kütüphaneler**

Projede kullanılan başlıca kütüphaneler:
- Flask
- Flask-SQLAlchemy
- Flask-Login
- sqlite3
- datetime

Ek olarak, projenin çalışması için gerekli diğer kütüphaneler `requirements.txt` dosyasında listelenmiştir. Bu dosyayı kullanarak gerekli kütüphaneleri tek seferde yükleyebilirsiniz:

```bash
pip install -r requirements.txt
```

## Çalıştırma

Uygulamayı başlatın:

```bash
python app.py
```

Tarayıcınızdan [http://localhost:5000](http://localhost:5000) adresine giderek uygulamayı kullanmaya başlayabilirsiniz.

## Dosya ve Klasörler

- **app.py:** Ana uygulama dosyası
- **chatbot.py:** Sohbet botu modülü
- **database.py:** Veritabanı işlemleri
- **elder_care_app.py:** Yaşlı bakım uygulaması ana fonksiyonları
- **medication_management.py:** İlaç yönetimi
- **reminder_management.py:** Hatırlatıcı sistemi
- **user_management.py:** Kullanıcı yönetimi
- **templates/:** HTML şablonları
- **static/:** Statik dosyalar (CSS, JS, resimler)
- **Screenshots/:** Ekran görüntüleri

## Katkıda Bulunma

Projeye katkıda bulunmak isterseniz, lütfen GitHub deposunu ziyaret edin ve "Fork" işlemi yaparak kendi değişikliklerinizi önerin. Katkılarınızı bekliyoruz!
