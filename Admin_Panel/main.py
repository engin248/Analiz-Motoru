# Streamlit Main App - Schema fix - v3
import os
import sys
# Streamlit Main App - Updated to fix imports
import streamlit as st
import time
import threading

# --- PATH CONFIG ---
# Analiz_Motoru root dizinine erişim
admin_panel_dir = os.path.dirname(os.path.abspath(__file__)) # .../Admin_Panel
analiz_motoru_root = os.path.dirname(admin_panel_dir) # .../Analiz-Motoru

# Admin_Panel klasörünü path'e ekle
if analiz_motoru_root not in sys.path:
    sys.path.insert(0, analiz_motoru_root)

# Kendi modüllerimizi içe aktaralım
from Admin_Panel.core.engine import start_permanent_scheduler, get_auth_hash
from Admin_Panel.styles.main_styles import apply_styles, apply_login_styles
from Admin_Panel.components.sidebar import render_sidebar

# View modüllerini içe aktaralım
from Admin_Panel.views.overview import render_overview
from Admin_Panel.views.logs import render_logs
from Admin_Panel.views.bot_control import render_bot_control

# --- PAGE CONFIG ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

st.set_page_config(
    page_title="Analiz Motoru - " + ("Dashboard" if st.session_state.get("authenticated") else "Giriş"),
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded" if st.session_state.get("authenticated") else "collapsed"
)

# --- SCHEDULER INITIALIZATION (CRITICAL: ROOT LEVEL) ---
with open("MAIN_INIT.txt", "w") as f: f.write("STEP_REACHED")
if not any(t.name == "SchedulerThread" for t in threading.enumerate()):
    start_permanent_scheduler()

# --- LOGIN SCREEN ---
def login_screen():
    apply_login_styles()
    c1, c2, c3 = st.columns([3, 2, 3])
    with c2:
        st.markdown('<div class="login-style"></div>', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/2593/2593491.png", width=90)
        st.markdown("<h1 style='margin: 10px 0 5px 0;'>Kontrol Merkezi</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; margin-bottom: 30px;'>Lütfen kimlik bilgilerinizi doğrulayın.</p>", unsafe_allow_html=True)
        user_input = st.text_input("Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
        pw_input = st.text_input("Şifre", type="password", placeholder="Şifrenizi girin")
        st.write("")
        if st.button("SİSTEME ERİŞİM SAĞLA", key="li_btn", type="primary", use_container_width=True):
            if user_input == "admin" and pw_input == "admin123":
                st.session_state["authenticated"] = True
                st.query_params["auth"] = get_auth_hash()
                st.success("✅ Erişim Yetkisi Verildi!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("🚫 Erişim Reddedildi: Bilgiler Hatalı.")

# --- AUTH CHECK ---
auth_token = st.query_params.get("auth")
if auth_token == get_auth_hash():
    st.session_state["authenticated"] = True

if not st.session_state["authenticated"]:
    login_screen()
    st.stop()
else:
    if st.query_params.get("auth") != get_auth_hash():
        st.query_params["auth"] = get_auth_hash()

# --- MAIN APP ---
apply_styles()

menu_options = ["🏠 Genel Bakış", "📜 Sistem Logları", "⚙️ Bot Kontrol"]
page = render_sidebar(menu_options, st.query_params.get("p", menu_options[0]))

if page != st.query_params.get("p"):
    st.query_params["p"] = page
    st.rerun()

# --- NAVIGATION ---
if page == "🏠 Genel Bakış":
    render_overview()
elif page == "📜 Sistem Logları":
    render_logs()
elif page == "⚙️ Bot Kontrol":
    render_bot_control()

st.write("---")
st.write("Analiz Motoru v1.0 | 2026")
