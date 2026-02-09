import streamlit as st
import base64
import os

def get_base64_img(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

def render_sidebar(menu_options, current_p):
    # Logo Scrapper klasörünün içinde
    current_file_path = os.path.abspath(__file__)
    components_dir = os.path.dirname(current_file_path)
    admin_panel_dir = os.path.dirname(components_dir)
    root_dir = os.path.dirname(admin_panel_dir)
    scrapper_root = os.path.join(root_dir, "Scrapper")
    logo_path = os.path.join(scrapper_root, "static", "app_logo.png")
    
    logo_base64 = get_base64_img(logo_path)
    
    # --- LUMORA PREMIUM SIDEBAR ---
    # Sidebar içine render edilmesi için 'with st.sidebar:' içine alıyoruz.
    with st.sidebar:
        st.markdown(f"""
            <style>
            /* Sidebar Ana Konteyner */
            [data-testid="stSidebar"] {{
                background-color: #0B0D11 !important;
                border-right: 1px solid rgba(0, 245, 160, 0.1) !important;
            }}

            /* Streamlit Blok Ayarları */
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{
                gap: 0 !important;
                padding: 0 !important;
            }}
            
            /* BRAND SECTION - PERFECT CENTERING */
            .brand-section {{
                padding: 34px 0 20px 0;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                width: 100%;
            }}
            
            .brand-logo-img {{
                width: 110px;
                height: 110px;
                border-radius: 50%;
                border: 2px solid rgba(75, 217, 158, 0.4);
                box-shadow: 0 0 30px rgba(75, 217, 158, 0.15);
                margin-bottom: 20px;
                object-fit: cover;
            }}
            
            .brand-text {{
                color: #FFF;
                font-size: 30px;
                font-weight: 950;
                letter-spacing: -1.5px;
                margin: 0 !important;
                line-height: 1;
            }}
            .brand-tagline {{
                color: #4BD99E;
                font-size: 10px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 3.5px;
                margin-top: 2px !important;
                opacity: 0.6;
                width: 100%;
            }}

            /* RADYO BUTONLARI - KESİN ÇÖZÜM */
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label div:first-child {{
                display: none !important;
            }}
            
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] {{
                padding: 20px 15px !important;
                gap: 12px !important;
            }}
            
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label {{
                background: rgba(255, 255, 255, 0.02) !important;
                border: 1px solid rgba(255, 255, 255, 0.04) !important;
                padding: 16px !important;
                border-radius: 14px !important;
                transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
                cursor: pointer !important;
                width: 100% !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }}
            
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {{
                width: 100% !important;
                text-align: center !important;
            }}
            
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label p {{
                color: #888 !important;
                font-size: 15px !important;
                font-weight: 500 !important;
                margin: 0 !important;
            }}
            
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label[data-selected="true"] {{
                background: rgba(75, 217, 158, 0.1) !important;
                border-color: rgba(75, 217, 158, 0.3) !important;
                box-shadow: 0 5px 15px rgba(0,0,0,0.3) !important;
            }}
            
            div[data-testid="stSidebar"] div.stRadio div[role="radiogroup"] label[data-selected="true"] p {{
                color: #4BD99E !important;
                font-weight: 800 !important;
            }}

            .sidebar-header {{
                font-size: 11px;
                color: #222;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 3px;
                text-align: center;
                width: 100%;
                padding: 40px 0 15px 0;
                opacity: 0.6;
            }}
            </style>
            
            <div class="brand-section">
                <img src="data:image/png;base64,{logo_base64}" class="brand-logo-img">
                <h1 class="brand-text">LUMORA</h1>
                <p class="brand-tagline">Analysis Engine</p>
            </div>
            <div class="sidebar-header">MAIN NAVIGATION</div>
        """, unsafe_allow_html=True)

        try:
            def_idx = menu_options.index(current_p)
        except:
            def_idx = 0

        page = st.radio("Nav", menu_options, index=def_idx, label_visibility="collapsed", key="nav_radio")
        
        # Alt Kısım Profil ve Çıkış - Flexbox ile en alta itiyoruz
        st.markdown("""
            <style>
            /* Sidebar'ın içindeki dikey bloğu flex-container yapıyoruz */
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
                display: flex;
                flex-direction: column;
                height: 95vh !important;
            }
            
            /* Profil kartını en alta iten sihirli komut: margin-top: auto */
            .user-profile-v8 {
                margin-top: auto !important;
                padding: 15px;
                background: rgba(75, 217, 158, 0.03);
                border: 1px solid rgba(75, 217, 158, 0.05);
                border-radius: 16px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                gap: 10px;
                margin: 20px 15px 10px 15px;
                text-align: center;
            }
            .user-avatar-v8 {
                width: 44px;
                height: 44px;
                background: linear-gradient(135deg, #4BD99E 0%, #17a671 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #000;
                font-weight: 900;
                box-shadow: 0 4px 15px rgba(75, 217, 158, 0.2);
                font-size: 18px;
            }
            
            /* Buton konteynerini de profile yapıştırıyoruz */
            div.stButton:has(button[key="logout_btn_sidebar"]) {
                margin: 0 15px 20px 15px !important;
            }
            </style>
            
            <div class="user-profile-v8">
                <div class="user-avatar-v8">E</div>
                <div>
                    <div style="color: #EEE; font-size: 15px; font-weight: 800; line-height: 1.2;">engin</div>
                    <div style="color: #4BD99E; font-size: 9px; text-transform: uppercase; margin-top: 5px; font-weight: 800; letter-spacing: 1.5px;">Lumora Architect</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Güvenli Çıkış", type="secondary", use_container_width=True, key="logout_btn_sidebar"):
            st.session_state["authenticated"] = False
            if "auth" in st.query_params:
                del st.query_params["auth"]
            st.rerun()
            
    return page
