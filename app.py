"""
app.py — لوحة التحكم الرئيسية (Streamlit)
شغّله بـ: streamlit run app.py
"""

import os
import streamlit as st
import database as db
from datetime import datetime

# ─── إعدادات الصفحة ───────────────────────────────────────────
st.set_page_config(
    page_title="Price Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BOT_USERNAME = os.environ.get("BOT_USERNAME", "MyPriceTracker11Bot")

# ─── CSS مخصص ────────────────────────────────────────────────
st.markdown("""
<style>
/* خطوط ونظام ألوان */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans Arabic', sans-serif;
    direction: rtl;
}

/* ألوان المشروع */
:root {
    --primary:   #1B4FFF;
    --primary-dark: #1239CC;
    --success:   #00B37E;
    --danger:    #E03B3B;
    --warning:   #F59E0B;
    --bg:        #F7F8FC;
    --card:      #FFFFFF;
    --border:    #E4E7EF;
    --text:      #1A1D2E;
    --muted:     #6B7280;
}

/* خلفية الصفحة */
.stApp { background: var(--bg); }

/* إخفاء عناصر Streamlit الافتراضية */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 1100px; }

/* هيدر الموقع */
.site-header {
    background: linear-gradient(135deg, #1B4FFF 0%, #0A2E99 100%);
    color: white;
    padding: 1.4rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.site-header h1 { margin: 0; font-size: 1.5rem; font-weight: 700; }
.site-header p  { margin: 0; font-size: 0.85rem; opacity: 0.8; }

/* بطاقات الإحصائيات */
.stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    text-align: center;
}
.stat-card .stat-num {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary);
    line-height: 1;
}
.stat-card .stat-label {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.3rem;
}

/* بطاقة التحقق */
.verify-card {
    background: #FFF8E7;
    border: 1.5px solid #F59E0B;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1.2rem;
}
.verify-card h3 { color: #B45309; margin: 0 0 0.5rem; font-size: 1rem; }
.verify-card p  { color: #78350F; margin: 0; font-size: 0.88rem; }

/* عناصر الجداول */
.url-row {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.87rem;
    word-break: break-all;
}
.url-row .url-text { color: var(--text); flex: 1; }
.url-row .url-label { color: var(--muted); font-size: 0.78rem; margin-top: 2px; }

/* بادج الفئة */
.badge {
    display: inline-block;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-left: 0.5rem;
}
.badge-store    { background: #EEF2FF; color: #4F46E5; }
.badge-compete  { background: #FEF3C7; color: #92400E; }

/* سجل التنبيهات */
.alert-row {
    background: var(--card);
    border-right: 4px solid var(--primary);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}
.alert-time { color: var(--muted); font-size: 0.75rem; margin-bottom: 0.3rem; }
.alert-url  { color: var(--primary); font-weight: 600; margin-bottom: 0.2rem; }
.alert-msg  { color: var(--text); white-space: pre-line; line-height: 1.5; }

/* أزرار Streamlit */
.stButton > button {
    background: var(--primary) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
}
.stButton > button:hover {
    background: var(--primary-dark) !important;
}

/* تنسيق نموذج الإدخال */
.stTextInput > div > div > input,
.stSelectbox > div > div > select {
    border-radius: 8px !important;
    border-color: var(--border) !important;
    direction: rtl !important;
}

/* رسائل النجاح والخطأ */
.stSuccess, .stError, .stInfo, .stWarning {
    border-radius: 10px !important;
}

/* تبويبات */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
.stTabs [data-baseweb="tab"] {
    background: var(--card) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: white !important;
    border-color: var(--primary) !important;
}

/* زر تليجرام */
.tg-btn {
    display: inline-block;
    background: #2CA5E0;
    color: white !important;
    text-decoration: none;
    padding: 0.6rem 1.4rem;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
    margin-top: 0.7rem;
}
.tg-btn:hover { background: #1A8FC5; }

/* سطر فاصل */
hr.divider {
    border: none;
    border-top: 1px solid var(--border);
    margin: 1.2rem 0;
}
</style>
""", unsafe_allow_html=True)


# ─── SESSION STATE ────────────────────────────────────────────
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "page" not in st.session_state:
    st.session_state.page = "login"  # login | register | dashboard


# ─── HELPERS ──────────────────────────────────────────────────

def go(page: str):
    st.session_state.page = page
    st.rerun()


def current_user():
    if st.session_state.user_id:
        return db.get_user_by_id(st.session_state.user_id)
    return None


def logout():
    st.session_state.user_id = None
    st.session_state.page = "login"
    st.rerun()


# ─── صفحة تسجيل الدخول ───────────────────────────────────────

def page_login():
    st.markdown("""
    <div class="site-header">
        <div>
            <h1>📊 Price Tracker</h1>
            <p>راقب أسعار منافسيك ومتجرك — 24/7</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("### 🔐 تسجيل الدخول")
        email    = st.text_input("البريد الإلكتروني", placeholder="example@email.com")
        password = st.text_input("الباسوورد", type="password")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("دخول ←", use_container_width=True):
                if not email or not password:
                    st.error("اكتب البريد والباسوورد")
                else:
                    user = db.authenticate(email, password)
                    if user:
                        st.session_state.user_id = user["id"]
                        go("dashboard")
                    else:
                        st.error("❌ البريد أو الباسوورد غلط")
        with col_b:
            if st.button("حساب جديد", use_container_width=True):
                go("register")


# ─── صفحة التسجيل ────────────────────────────────────────────

def page_register():
    st.markdown("""
    <div class="site-header">
        <div>
            <h1>📊 Price Tracker</h1>
            <p>إنشاء حساب جديد</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("### 📝 إنشاء حساب جديد")
        name     = st.text_input("الاسم الكامل",      placeholder="محمد أحمد")
        email    = st.text_input("البريد الإلكتروني", placeholder="example@email.com")
        password = st.text_input("الباسوورد",         type="password", placeholder="8 أحرف على الأقل")
        confirm  = st.text_input("تأكيد الباسوورد",   type="password")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("إنشاء الحساب ←", use_container_width=True):
                if not name or not email or not password:
                    st.error("كل الحقول مطلوبة")
                elif len(password) < 8:
                    st.error("الباسوورد 8 أحرف على الأقل")
                elif password != confirm:
                    st.error("الباسوردين مش متطابقين")
                else:
                    uid = db.create_user(name, email, password)
                    if uid is None:
                        st.error("❌ البريد ده مسجّل بالفعل")
                    else:
                        st.session_state.user_id = uid
                        st.success("✅ تم إنشاء حسابك!")
                        go("dashboard")
        with col_b:
            if st.button("لدي حساب", use_container_width=True):
                go("login")


# ─── لوحة التحكم الرئيسية ────────────────────────────────────

def page_dashboard():
    user = current_user()
    if not user:
        go("login")
        return

    # هيدر مع اسم المستخدم وزر خروج
    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.markdown(f"""
        <div class="site-header">
            <div>
                <h1>📊 Price Tracker</h1>
                <p>أهلاً {user['name']} — حسابك {'✅ مفعّل' if user['is_verified'] else '⏳ بانتظار التفعيل'}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_h2:
        st.write("")
        st.write("")
        if st.button("خروج 🚪", use_container_width=True):
            logout()

    # ── تنبيه التحقق لو الحساب مش مفعّل ──────────────────────
    if not user["is_verified"]:
        st.markdown(f"""
        <div class="verify-card">
            <h3>⚠️ حسابك بانتظار التفعيل عبر التليجرام</h3>
            <p>اضغط الزر أدناه لتفعيل حسابك وربطه بالتليجرام — خطوة واحدة بس!</p>
        </div>
        """, unsafe_allow_html=True)

        link_token = user["link_token"]
        tg_link    = f"https://t.me/{BOT_USERNAME}?start={link_token}"

        st.markdown(f"""
        <a href="{tg_link}" target="_blank" class="tg-btn">
            🚀 تفعيل الحساب وربط التليجرام
        </a>
        """, unsafe_allow_html=True)

        st.markdown("<small style='color:#6B7280;'>بعد الضغط هيفتح معك التليجرام تلقائياً — وافق على مشاركة رقمك وخلاص ✅</small>", unsafe_allow_html=True)

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)

        if st.button("🔄 تحديث حالة الحساب"):
            st.rerun()

    # ── إحصائيات ───────────────────────────────────────────────
    urls    = db.get_urls_for_user(user["id"])
    alerts  = db.get_alerts_for_user(user["id"])
    my_urls = [u for u in urls if u["category"] == "my_store"]
    cp_urls = [u for u in urls if u["category"] == "competitor"]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{len(my_urls)}</div>
            <div class="stat-label">📦 منتجات متجري</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{len(cp_urls)}</div>
            <div class="stat-label">🔍 مراقبة منافسين</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-num">{len(alerts)}</div>
            <div class="stat-label">🔔 إجمالي التنبيهات</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ── التبويبات ──────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "📦 منتجات متجري",
        "🔍 مراقبة المنافسين",
        "🔔 سجل التنبيهات",
    ])

    with tab1:
        _url_section(user, "my_store", my_urls,
                     placeholder="https://متجري.com/product/اسم-المنتج",
                     description="هنا تتابع أسعار منتجاتك — هتتنبّه فور ما يتغيّر أي سعر بالخطأ أو بدون علمك")

    with tab2:
        _url_section(user, "competitor", cp_urls,
                     placeholder="https://منافس.com/product/اسم-المنتج",
                     description="هنا تضيف روابط منافسيك — هتعرف فور ما يغيّروا أي سعر")

    with tab3:
        _alerts_section(alerts)


def _url_section(user, category: str, urls: list, placeholder: str, description: str):
    st.markdown(f"<p style='color:#6B7280;font-size:0.88rem;'>{description}</p>", unsafe_allow_html=True)

    # إضافة رابط جديد
    with st.expander("➕ إضافة رابط جديد", expanded=len(urls) == 0):
        new_url   = st.text_input("رابط المنتج",  placeholder=placeholder,
                                   key=f"new_url_{category}")
        new_label = st.text_input("اسم مميز (اختياري)", placeholder="مثلاً: سماعة بلوتوث XYZ",
                                   key=f"new_label_{category}")
        if st.button("إضافة الرابط", key=f"add_{category}"):
            if not new_url.startswith("http"):
                st.error("الرابط لازم يبدأ بـ https://")
            else:
                ok = db.add_url(user["id"], new_url, category, new_label)
                if ok:
                    st.success("✅ تم إضافة الرابط!")
                    st.rerun()
                else:
                    st.warning("⚠️ الرابط ده مضاف بالفعل")

    # قائمة الروابط
    if not urls:
        st.info("مفيش روابط مضافة بعد — أضف الأول من فوق ⬆️")
        return

    for row in urls:
        col_u, col_d = st.columns([5, 1])
        with col_u:
            label_text = f" — {row['label']}" if row['label'] else ""
            st.markdown(f"""
            <div class="url-row">
                <div>
                    <div class="url-text">{row['url']}</div>
                    <div class="url-label">{label_text or 'بدون اسم'} &nbsp;|&nbsp; مضاف {row['created_at'][:10]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_d:
            if st.button("🗑", key=f"del_{row['id']}", help="حذف الرابط"):
                db.delete_url(row["id"], user["id"])
                st.rerun()


def _alerts_section(alerts: list):
    if not alerts:
        st.info("مفيش تنبيهات بعد — هتيجيلك هنا وعلى تليجرام فور ما يتغير أي سعر 🔔")
        return

    for alert in alerts:
        # استخراج سطر أول من الرسالة كعنوان
        msg_lines = alert["message"].strip().split("\n")
        title_line = msg_lines[1] if len(msg_lines) > 1 else msg_lines[0]
        # إزالة markdown
        import re
        clean_title = re.sub(r'[\*\[\]`]', '', title_line).strip()

        st.markdown(f"""
        <div class="alert-row">
            <div class="alert-time">🕐 {alert['sent_at'][:16].replace('T', ' ')}</div>
            <div class="alert-url">{clean_title}</div>
            <div class="alert-msg">{alert['message'].replace(msg_lines[0], '').replace(msg_lines[1] if len(msg_lines)>1 else '', '', 1).strip()}</div>
        </div>
        """, unsafe_allow_html=True)


# ─── ROUTER ───────────────────────────────────────────────────

def main():
    page = st.session_state.get("page", "login")
    if st.session_state.user_id and page not in ("dashboard",):
        page = "dashboard"

    if page == "login":
        page_login()
    elif page == "register":
        page_register()
    else:
        page_dashboard()


main()
