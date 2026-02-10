import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
        /* GENEL SAYFA */
        [data-testid="stAppViewContainer"] {
            background-color: #0E1117;
        }
        
        /* MERTİK KUTULARI (KARTLAR) */
        div[data-testid="stMetric"] {
            background-color: #333333 !important; /* Belirgin Kutu Rengi */
            padding: 15px 10px !important;
            border-radius: 12px !important;
            border: 1px solid #555555 !important;
            text-align: center !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
            min-height: 120px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
        }
        
        div[data-testid="stMetricLabel"] {
            color: #B2B5BE !important;
            font-size: 14px !important;
            font-weight: 500;
            margin-bottom: 5px;
            text-align: center !important; /* Zorla Ortala */
            width: 100%;
        }
        
        div[data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 28px !important;
            font-weight: 700;
            font-family: 'Inter', sans-serif;
            text-align: center !important; /* Zorla Ortala */
            width: 100%;
        }
        
        /* Delta (Değişim) Yazısı */
        div[data-testid="stMetricDelta"] {
            justify-content: center !important; /* Oku Ortala */
        }
        
        /* TABLO STİLİ */
        [data-testid="stDataFrame"] {
            border: 1px solid #41444C;
            border-radius: 8px;
        }
        
        /* BAŞLIKLAR */
        h1, h2, h3 {
            color: #FAFAFA !important;
            font-family: 'Inter', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

def apply_login_styles():
    st.markdown("""
        <style>
        /* Arka planı tamamen karart ve gradyan ekle */
        [data-testid="stAppViewContainer"] {
            background-image: radial-gradient(circle at 20% 30%, #1a1c23 0%, #0e1117 100%);
        }
        
        /* Giriş kartını güzelleştir */
        [data-testid="stVerticalBlock"] > div:has(div.login-style) {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 50px !important;
            border-radius: 24px !important;
            backdrop-filter: blur(15px);
            box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        }
        
        /* Inputları özelleştir */
        .stTextInput > div > div > input {
            background-color: rgba(0,0,0,0.2) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-radius: 10px !important;
            padding: 12px 15px !important;
        }
        
        h1 {
            letter-spacing: -1px;
            font-weight: 800 !important;
        }
        </style>
    """, unsafe_allow_html=True)

def apply_bot_card_styles():
    st.markdown("""
    <style>
        /* Streamlit'in kenarlıklı konteynerini (st.container border=True) yakalayıp beyaza çeviriyoruz */
        /* Streamlit'in kenarlıklı konteynerini (st.container border=True) yakalayıp beyaza çeviriyoruz */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 2px solid #333 !important;
            border-radius: 24px !important;
            background-color: #161616 !important; /* Lacivertliği kırmak için neredeyse siyah gri */
            padding: 2px !important;
        }
        
        /* Popover (Kalem) Butonunu Küçültme */
        div[data-testid="stPopover"] > button {
            padding: 0px 5px !important;
            min-height: 22px !important;
            height: 22px !important;
            width: 30px !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            background: rgba(255,255,255,0.05) !important;
            margin-top: 5px !important;
        }

        .bot-card-content {
            padding: 20px;
        }

        .status-strip-v8 {
            height: 6px;
            width: 60px;
            border-radius: 3px;
            margin-bottom: 20px;
        }
        .bg-running-v8 { background: #00F5A0; box-shadow: 0 0 15px rgba(0,245,160,0.5); }
        .bg-waiting-v8 { background: #FFA500; box-shadow: 0 0 15px rgba(255,165,0,0.3); }
        .bg-stopped-v8 { background: #666; }
        
        .b-title-v8 { font-size: 19px; font-weight: 800; color: #FFF; margin-bottom: 0px; white-space: nowrap; }
        .b-sub-v8 { font-size: 9px; color: #666; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 2px; }
        
        .b-badge-v8 {
            font-size: 11px;
            font-weight: 900;
            padding: 6px 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            display: inline-block;
            margin-top: -10px;
        }
        .badge-active-v8 { background: rgba(0,245,160,0.15); color: #00F5A0; border-color: rgba(0,245,160,0.3); }
        .badge-waiting-v8 { background: rgba(255,165,0,0.15); color: #FFA500; border-color: rgba(255,165,0,0.3); }
        .badge-passive-v8 { background: rgba(255,255,255,0.05); color: #888; border-color: rgba(255,255,255,0.1); }

        /* ÇÖP KUTUSU - BUTONUN KENDİSİNİ VE ARKASINI KIRMIZI YAP */
        div:has(> .trash-btn-mark-final) + div button,
        .trash-btn-mark-final ~ div button,
        button:has(p:contains("🗑️")) {
            background-color: #FF4B4B !important;
            color: white !important;
            border: none !important;
            min-height: 32px !important;
            height: 32px !important;
            width: 32px !important;
            padding: 0 !important;
            margin: 0 !important;
            margin-top: -10px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4) !important;
        }
        
        div:has(> .trash-btn-mark-final) + div button:hover {
            background-color: #FF1E1E !important;
            transform: scale(1.1);
        }

        /* İkonun Kendisini Ortalama */
        div:has(> .trash-btn-mark-final) + div button p {
            color: white !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 16px !important;
            line-height: 1 !important;
            display: block !important;
            width: 100% !important;
            text-align: center !important;
        }

        .metric-pill-v8 {
            background: #262626; /* Inputlarla aynı renk */
            border: 1px solid #444;
            padding: 15px;
            border-radius: 18px;
            text-align: center;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.5); /* Hafif iç gölge ile derinlik */
        }
        .m-val-v8 { font-size: 22px; font-weight: 800; color: #00F5A0; line-height: 1; }
        .m-lab-v8 { font-size: 9px; color: #888; font-weight: 700; margin-top: 6px; text-transform: uppercase; }
        
        .url-box-v8 {
            font-size: 9px; 
            color: #888;
            background: #262626;  /* Inputlarla aynı renk */
            padding: 8px 12px; 
            border-radius: 10px; 
            border: 1px solid #444;
            margin: 15px 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .plat-badge-v8 {
            font-size: 12px;
            font-weight: 900;
            padding: 6px 20px;
            border-radius: 10px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            margin-top: -50px;
        }

        .plat-trendyol { background: #F27A1A; color: white; border: 1px solid #ff8a3d; }
        .plat-amazon { background: #FF9900; color: black; border: 1px solid #ffb340; }
        /* Secondary Butonlar (Planla, Ayarlar, Uyarı) - Koyu Tema */
        button[kind="secondary"] {
            background-color: #262626 !important;
            border: 1px solid #444 !important;
            color: #E0E0E0 !important;
            transition: all 0.2s ease;
        }
        button[kind="secondary"]:hover {
            border-color: #666 !important;
            background-color: #333 !important;
            color: white !important;
        }
        
        /* Ayarlar (Popover) butonu */
        div[data-testid="stPopover"] > button {
           background-color: #262626 !important;
           border: 1px solid #444 !important;
           color: #E0E0E0 !important;
        }

        /* UYARI BUTONU (Siyah ama ikon sarı/kırmızı olabilir) */
        /* Normal secondary override yeterli */

        /* INPUT ALANLARINI (Kutucukları) KART RENGİNE UYDURMA */
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"],
        .stTimeInput input,
        .stTextInput input {
            background-color: #262626 !important; /* Karttan biraz daha koyu */
            border: 1px solid #444 !important;
            color: white !important;
            border-radius: 8px !important;
        }
        
        /* Dropdown ok işareti ve diğer ikonlar */
        div[data-baseweb="select"] svg,
        .stTimeInput svg {
            fill: #888 !important;
        }
    </style>
    """, unsafe_allow_html=True)
