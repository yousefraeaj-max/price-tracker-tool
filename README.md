# 📊 Price Tracker Platform — متعدد المستخدمين

بوت تليجرام + موقع ويب كامل لمراقبة أسعار منافسيك ومنتجاتك 24/7.

---

## 📁 ملفات المشروع

| الملف | الوظيفة |
|-------|---------|
| `app.py` | موقع الويب ولوحة التحكم (Streamlit) |
| `bot.py` | بوت التليجرام (التحقق + التنبيهات) |
| `scraper.py` | فاحص الأسعار (يشتغل في الخلفية) |
| `database.py` | قاعدة البيانات SQLite |
| `main.py` | يشغّل البوت والـ scraper معاً |
| `requirements.txt` | المكتبات المطلوبة |
| `Procfile` | إعدادات Railway |

---

## 🚀 رفع على Railway

### الخطوة ١ — GitHub

1. روح [github.com](https://github.com) → **New repository** → اسمه `price-tracker`
2. اضغط **uploading an existing file**
3. ارفع كل الملفات السبعة دي
4. اضغط **Commit changes**

### الخطوة ٢ — Railway

1. روح [railway.app](https://railway.app) → سجّل بحسابك على GitHub
2. **New Project** → **Deploy from GitHub repo** → اختار `price-tracker`

### الخطوة ٣ — Variables (مهم جداً!)

في Railway → مشروعك → تبويب **Variables** → أضف:

| الاسم | القيمة |
|-------|--------|
| `TELEGRAM_TOKEN` | التوكن من @BotFather |
| `BOT_USERNAME` | `MyPriceTracker11Bot` |
| `CHECK_INTERVAL_SECONDS` | `300` |

### الخطوة ٤ — تشغيل سيرفيسين

في Railway لازم تضيف **سيرفيس ثاني** للـ worker:
1. في مشروعك → **Add Service** → **GitHub Repo** (نفس الـ repo)
2. غيّر الـ Start Command لـ: `python main.py`

أو ببساطة: **الـ web** بيشغّل `app.py` والـ **worker** بيشغّل `main.py`.

---

## 📲 إزاي يشتغل النظام

```
المستخدم يسجّل على الموقع
       ↓
يضغط "تفعيل الحساب وربط التليجرام"
       ↓
يفتح التليجرام على البوت تلقائياً
       ↓
يوافق على مشاركة رقم هاتفه
       ↓
الحساب يتفعّل ✅ وهيبدأ يستقبل تنبيهات
       ↓
يضيف روابط منتجاته ومنافسيه
       ↓
البوت يبعتله تنبيه فور ما يتغيّر أي سعر 🔔
```

---

## 📩 شكل التنبيهات

```
🔔 تغيير سعر!
🌐 سماعات ترجمة فورية

📉 قطعة واحدة - 149 جنيه
   كان: 199.00 ← بقى: 149.00
   انخفض بنسبة 25.1%
```
