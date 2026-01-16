import streamlit as st
import yt_dlp
import logging
import os
import sys
import time
import tempfile
import base64
from datetime import datetime
import streamlit.components.v1 as components
import re
from pathlib import Path

# --- 1. Configuration & Constants ---

PLATFORMS = {
    'youtube': {'name': 'YouTube', 'icon': '🔴', 'pattern': r'(youtube\.com|youtu\.be)'},
    'tiktok': {'name': 'TikTok', 'icon': '🎵', 'pattern': r'tiktok\.com'},
    'instagram': {'name': 'Instagram', 'icon': '📸', 'pattern': r'instagram\.com'},
    'twitter': {'name': 'X/Twitter', 'icon': '🐦', 'pattern': r'(twitter\.com|x\.com)'},
    'facebook': {'name': 'Facebook', 'icon': '📘', 'pattern': r'facebook\.com'},
    'vimeo': {'name': 'Vimeo', 'icon': '🎬', 'pattern': r'vimeo\.com'},
    'twitch': {'name': 'Twitch', 'icon': '💜', 'pattern': r'twitch\.tv'},
    'reddit': {'name': 'Reddit', 'icon': '🟠', 'pattern': r'reddit\.com'},
    'dailymotion': {'name': 'Dailymotion', 'icon': '🌐', 'pattern': r'dailymotion\.com'},
    'other': {'name': 'אחר', 'icon': '🌍', 'pattern': r'.*'}
}

AUDIO_QUALITIES = {
    '🎵 320kbps (הכי טוב)': '320',
    '🎶 192kbps (מומלץ)': '192',
    '🔊 128kbps (בסיסי)': '128'
}

# --- 2. Logging Setup ---

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("UniversalDownloader")

def log_message(msg):
    logger.info(msg)

# --- 3. Page Config ---

st.set_page_config(
    page_title="מוריד המדיה האוניברסלי",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 4. Premium CSS Styles ---

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&family=Rubik:wght@400;500;600;700&display=swap');

    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-card: rgba(25, 25, 35, 0.8);
        --text-primary: #ffffff;
        --text-secondary: #a0a0b0;
        --accent-1: #ff3366;
        --accent-2: #8b5cf6;
        --accent-3: #00d4ff;
        --glass-border: rgba(255, 255, 255, 0.1);
        --glow-1: rgba(255, 51, 102, 0.4);
        --glow-2: rgba(139, 92, 246, 0.4);
    }

    .stApp {
        direction: rtl;
        text-align: right;
        font-family: 'Heebo', sans-serif;
        background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1a2e 50%, #0f0f1a 100%);
        min-height: 100vh;
    }
    
    /* Animated background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 80%, var(--glow-1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, var(--glow-2) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(0, 212, 255, 0.1) 0%, transparent 50%);
        pointer-events: none;
        z-index: -1;
        animation: pulse 8s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.6; }
        50% { opacity: 1; }
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Rubik', sans-serif;
        font-weight: 700;
        color: var(--text-primary) !important;
        text-align: right !important;
    }
    
    /* Main Title */
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2), var(--accent-3));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center !important;
        margin-bottom: 0.5rem;
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.2); }
    }
    
    .subtitle {
        text-align: center !important;
        color: var(--text-secondary);
        font-size: 1rem;
        margin-bottom: 2rem;
    }

    /* Glass Card */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.4),
            0 0 30px var(--glow-1),
            inset 0 1px 0 rgba(255, 255, 255, 0.15);
    }

    /* Platform Badge */
    .platform-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, var(--accent-2), var(--accent-1));
        padding: 8px 16px;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        color: white;
        margin-bottom: 1rem;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        direction: rtl; 
        text-align: right;
        border-radius: 15px !important;
        border: 2px solid var(--glass-border) !important;
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        padding: 15px 20px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-1) !important;
        box-shadow: 0 0 20px var(--glow-1) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-secondary) !important;
    }

    /* Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 15px !important;
        background: linear-gradient(135deg, var(--accent-1) 0%, var(--accent-2) 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.9rem 2rem !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        font-family: 'Heebo', sans-serif !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px var(--glow-1) !important;
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px var(--glow-1) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Download Button - Special Green */
    .stDownloadButton > button {
        width: 100%;
        border-radius: 15px !important;
        background: linear-gradient(135deg, #00c853 0%, #00bfa5 100%) !important;
        color: white !important;
        border: none !important;
        padding: 1rem 2rem !important;
        font-size: 20px !important;
        font-weight: 700 !important;
        font-family: 'Heebo', sans-serif !important;
        box-shadow: 0 4px 20px rgba(0, 200, 83, 0.4) !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 30px rgba(0, 200, 83, 0.5) !important;
    }

    /* Selectbox & Radio */
    .stSelectbox > div > div, .stRadio > div {
        direction: rtl;
        text-align: right;
    }
    
    .stSelectbox > div > div > div {
        background: var(--bg-secondary) !important;
        border: 2px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    .stRadio > div > label {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 10px !important;
        padding: 10px 15px !important;
        margin: 5px !important;
        transition: all 0.3s ease !important;
    }
    
    .stRadio > div > label:hover {
        border-color: var(--accent-1) !important;
        box-shadow: 0 0 15px var(--glow-1) !important;
    }
    
    label {
        font-weight: 500 !important;
        font-size: 1rem !important;
        color: var(--text-primary) !important;
    }

    /* Progress Bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-1), var(--accent-2), var(--accent-3)) !important;
        animation: progressGlow 2s ease-in-out infinite;
    }
    
    @keyframes progressGlow {
        0%, 100% { filter: brightness(1); }
        50% { filter: brightness(1.3); }
    }

    /* Success/Error/Warning Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 12px !important;
        backdrop-filter: blur(10px) !important;
    }

    /* Thumbnail */
    .stImage img {
        border-radius: 15px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    .stImage img:hover {
        transform: scale(1.02) !important;
    }

    /* Metrics */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 15px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--accent-3);
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 5px;
    }

    /* Section Header */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--glass-border);
    }
    
    .section-header h3 {
        margin: 0;
        font-size: 1.2rem;
    }

    /* Generic Fixes */
    p, .stMarkdown {
        text-align: right !important;
        color: var(--text-secondary);
    }
    
    div[data-testid="stVerticalBlock"] > div {
        align-items: flex-end;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
        margin: 2rem 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 10px !important;
        color: var(--text-secondary) !important;
        padding: 10px 20px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-1), var(--accent-2)) !important;
        color: white !important;
        border: none !important;
    }
    
    /* Sidebar Fixes */
    [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
        background: var(--bg-secondary) !important;
        border-left: 1px solid var(--glass-border) !important;
        min-width: 0 !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: var(--bg-secondary) !important;
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
    }
    
    [data-testid="stSidebar"][aria-expanded="false"] > div {
        display: none !important;
    }
    
    [data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 280px !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
    """, unsafe_allow_html=True)

# --- 5. Helper Functions ---

def detect_platform(url):
    """Detect the platform from URL"""
    for platform_id, platform_info in PLATFORMS.items():
        if re.search(platform_info['pattern'], url, re.IGNORECASE):
            return platform_id, platform_info
    return 'other', PLATFORMS['other']

def format_duration(seconds):
    """Format duration in human readable format"""
    if not seconds or not isinstance(seconds, (int, float)):
        return "לא ידוע"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"

def format_filesize(bytes_size):
    """Format file size in human readable format"""
    if not bytes_size:
        return "לא ידוע"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.1f} TB"

def get_available_subtitles(info):
    """Get available subtitles"""
    subtitles = info.get('subtitles', {})
    auto_captions = info.get('automatic_captions', {})
    all_subs = {}
    
    for lang, subs in subtitles.items():
        all_subs[f"📝 {lang}"] = lang
    for lang, subs in auto_captions.items():
        all_subs[f"🤖 {lang} (אוטומטי)"] = lang
    
    return all_subs

# --- 6. Core Functions ---

def get_info(url):
    log_message(f"Starting metadata extraction for URL: {url}")
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            log_message(f"Metadata extracted successfully. Title: {info.get('title')}")
            return info
    except Exception as e:
        log_message(f"Error extracting metadata: {str(e)}")
        st.error(f"❌ שגיאה בחילוץ מידע: {str(e)}")
        return None

def download_media(url, options, progress_bar, status_text, temp_dir):
    """Download media to temp directory and return file path"""
    log_message(f"Download started. Options: {list(options.keys())}")
    options['noplaylist'] = True
    
    downloaded_file = None
    
    def progress_hook(d):
        nonlocal downloaded_file
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '0%').replace('%', '').strip()
                progress = min(float(p) / 100, 1.0)
                progress_bar.progress(progress)
                speed = d.get('_speed_str', 'N/A')
                eta = d.get('_eta_str', 'N/A')
                status_text.markdown(f"""
                <div style="text-align: center; color: #a0a0b0;">
                    <span style="font-size: 1.5rem; color: #00d4ff;">{d.get('_percent_str', '0%')}</span>
                    <br/>
                    <span>⚡ מהירות: {speed} | ⏱️ נותר: {eta}</span>
                </div>
                """, unsafe_allow_html=True)
            except:
                pass
        elif d['status'] == 'finished':
            downloaded_file = d.get('filename')
            progress_bar.progress(1.0)
            status_text.markdown("""
            <div style="text-align: center; color: #00d4ff; font-size: 1.2rem;">
                ✨ ההורדה הושלמה! מעבד קובץ סופי...
            </div>
            """, unsafe_allow_html=True)
            log_message(f"Download finished: {downloaded_file}")

    options['progress_hooks'] = [progress_hook]
    options['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            result_info = ydl.extract_info(url, download=True)
            
        # Find the downloaded file
        if downloaded_file and os.path.exists(downloaded_file):
            return downloaded_file, result_info
            
        # Fallback: search in temp dir
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                return file_path, result_info
                
        log_message("Processing complete.")
        return None, result_info
    except Exception as e:
        log_message(f"Download failed: {str(e)}")
        st.error(f"❌ שגיאה בהורדה: {str(e)}")
        return None, None

# --- 7. Initialize Session State ---

if 'video_info' not in st.session_state:
    st.session_state.video_info = None
if 'url_input' not in st.session_state:
    st.session_state.url_input = ""
if 'download_history' not in st.session_state:
    st.session_state.download_history = []

# --- 8. Main UI ---

# Header
st.markdown('<h1 class="main-title">🚀 מוריד המדיה האוניברסלי</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">הורד וידאו ואודיו מכל פלטפורמה באיכות הגבוהה ביותר</p>', unsafe_allow_html=True)

# Supported platforms info
with st.expander("📱 פלטפורמות נתמכות"):
    st.markdown("""
    **YouTube** • **TikTok** • **Instagram** • **Twitter/X** • **Facebook** • **Vimeo** • **Twitch** • **Reddit** • **Dailymotion** ומאות אתרים נוספים!
    """)

# Main content
st.markdown('<div class="section-header"><span>🔗</span><h3>הדבק קישור</h3></div>', unsafe_allow_html=True)

url = st.text_input(
    "URL", 
    value=st.session_state.url_input, 
    label_visibility="collapsed", 
    placeholder="הדבק כאן קישור מ-YouTube, TikTok, Instagram ועוד..."
)

col1, col2 = st.columns([3, 1])
with col1:
    check_button = st.button("🔍 בדוק קישור", use_container_width=True)
with col2:
    if st.button("🗑️", use_container_width=True, help="נקה"):
        st.session_state.url_input = ""
        st.session_state.video_info = None
        st.rerun()

if check_button:
    if url:
        st.session_state.url_input = url
        st.session_state.video_info = None
        log_message(f"User check URL: {url}")
        
        # Detect platform
        platform_id, platform_info = detect_platform(url)
        
        with st.spinner("⏳ מחלץ מידע..."):
            info = get_info(url)
            if info:
                st.session_state.video_info = info
                st.session_state.platform = platform_info
    else:
        st.warning("⚠️ אנא הדבק קישור תקין")

# Results Area
if st.session_state.video_info:
    info = st.session_state.video_info
    platform_info = st.session_state.get('platform', PLATFORMS['other'])
    
    st.markdown("---")
    
    # Platform badge
    st.markdown(f"""
    <div class="platform-badge">
        <span>{platform_info['icon']}</span>
        <span>{platform_info['name']}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Video Info Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    col_img, col_txt = st.columns([1, 1.5])
    
    with col_img:
        if info.get('thumbnail'):
            st.image(info['thumbnail'], use_container_width=True)
    
    with col_txt:
        st.markdown(f"### {info.get('title', 'ללא כותרת')}")
        st.markdown(f"**👤 מעלה:** {info.get('uploader', 'לא ידוע')}")
        
        # Stats row
        duration = format_duration(info.get('duration'))
        views = info.get('view_count', 0)
        likes = info.get('like_count', 0)
        
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">⏱️ {duration}</div>
                <div class="metric-label">משך</div>
            </div>
            """, unsafe_allow_html=True)
        with col_s2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">👁️ {views:,}</div>
                <div class="metric-label">צפיות</div>
            </div>
            """, unsafe_allow_html=True)
        with col_s3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">❤️ {likes:,}</div>
                <div class="metric-label">לייקים</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Download Settings
    st.markdown('<div class="section-header"><span>⚙️</span><h3>הגדרות הורדה</h3></div>', unsafe_allow_html=True)
    
    tabs = st.tabs(["🎬 וידאו", "🎵 אודיו"])
    
    with tabs[0]:  # Video tab
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        resolution_map = {
            "🌟 הכי טוב (Best)": "bestvideo+bestaudio/best",
            "📺 4K (2160p)": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "🖥️ Full HD (1080p)": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "📹 HD (720p)": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "📱 SD (480p)": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "📟 Low (360p)": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        }
        
        selected_res = st.selectbox(
            "📐 בחר איכות וידאו:",
            list(resolution_map.keys()),
            index=2
        )
        
        # Subtitles option
        available_subs = get_available_subtitles(info)
        download_subs = st.checkbox("📝 הורד כתוביות", value=False)
        
        selected_sub_lang = None
        if download_subs and available_subs:
            selected_sub_lang = st.selectbox(
                "בחר שפת כתוביות:",
                list(available_subs.keys())
            )
        elif download_subs:
            st.info("אין כתוביות זמינות לסרטון זה")
        
        if st.button("⬇️ הורד וידאו", key="download_video", use_container_width=True):
            ydl_opts = {
                'format': resolution_map[selected_res],
                'merge_output_format': 'mp4',
            }
            
            if download_subs and selected_sub_lang and available_subs:
                lang_code = available_subs[selected_sub_lang]
                ydl_opts['writesubtitles'] = True
                ydl_opts['subtitleslangs'] = [lang_code]
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path, result = download_media(url, ydl_opts, progress_bar, status_text, temp_dir)
                
                if file_path and os.path.exists(file_path):
                    st.balloons()
                    st.success("✅ ההורדה הושלמה בהצלחה!")
                    
                    # Read file for download
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    
                    file_name = os.path.basename(file_path)
                    file_size = len(file_data)
                    
                    st.info(f"📁 **גודל קובץ:** {format_filesize(file_size)}")
                    
                    # Download button
                    st.download_button(
                        label="📥 לחץ כאן להורדה למחשב",
                        data=file_data,
                        file_name=file_name,
                        mime="video/mp4",
                        use_container_width=True
                    )
                    
                    # Add to history
                    st.session_state.download_history.append({
                        'title': info.get('title', 'Unknown')[:40],
                        'icon': '🎬',
                        'time': datetime.now().strftime('%H:%M'),
                        'type': 'video'
                    })
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tabs[1]:  # Audio tab
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        col_fmt, col_quality = st.columns(2)
        
        with col_fmt:
            format_map = {"MP3": "mp3", "M4A": "m4a", "WAV": "wav"}
            selected_fmt = st.selectbox("🎵 פורמט:", list(format_map.keys()))
        
        with col_quality:
            selected_quality = st.selectbox("🔊 איכות:", list(AUDIO_QUALITIES.keys()), index=1)
        
        if st.button("⬇️ הורד אודיו", key="download_audio", use_container_width=True):
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format_map[selected_fmt],
                    'preferredquality': AUDIO_QUALITIES[selected_quality],
                }]
            }
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with tempfile.TemporaryDirectory() as temp_dir:
                file_path, result = download_media(url, ydl_opts, progress_bar, status_text, temp_dir)
                
                if file_path and os.path.exists(file_path):
                    st.balloons()
                    st.success("✅ ההורדה הושלמה בהצלחה!")
                    
                    # Find the converted audio file
                    audio_extensions = ['.mp3', '.m4a', '.wav', '.ogg']
                    final_file = None
                    
                    for f in os.listdir(temp_dir):
                        if any(f.endswith(ext) for ext in audio_extensions):
                            final_file = os.path.join(temp_dir, f)
                            break
                    
                    if not final_file:
                        final_file = file_path
                    
                    if os.path.exists(final_file):
                        with open(final_file, 'rb') as f:
                            file_data = f.read()
                        
                        file_name = os.path.basename(final_file)
                        file_size = len(file_data)
                        
                        st.info(f"📁 **גודל קובץ:** {format_filesize(file_size)}")
                        
                        # Download button
                        st.download_button(
                            label="📥 לחץ כאן להורדה למחשב",
                            data=file_data,
                            file_name=file_name,
                            mime=f"audio/{format_map[selected_fmt]}",
                            use_container_width=True
                        )
                        
                        # Add to history
                        st.session_state.download_history.append({
                            'title': info.get('title', 'Unknown')[:40],
                            'icon': '🎵',
                            'time': datetime.now().strftime('%H:%M'),
                            'type': 'audio'
                        })
        
        st.markdown('</div>', unsafe_allow_html=True)

# Download History (in sidebar)
with st.sidebar:
    st.markdown("### 📋 היסטוריית הורדות")
    if st.session_state.download_history:
        for item in reversed(st.session_state.download_history[-10:]):
            st.markdown(f"{item['icon']} {item['title']}... ({item['time']})")
    else:
        st.info("אין הורדות עדיין")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.85rem; padding: 1rem;">
    <p>🚀 מוריד המדיה האוניברסלי</p>
    <p style="font-size: 0.75rem;">תומך ב-YouTube, TikTok, Instagram, Twitter/X ועוד מאות אתרים</p>
</div>
""", unsafe_allow_html=True)
