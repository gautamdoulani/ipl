"""Shared utilities for IPL Explorer app."""

import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import os
import requests

# Database connection - use writable path for Streamlit Cloud
DB_PATH = Path(__file__).parent / "ipl.duckdb"

# For Streamlit Cloud, copy to tmp if needed (since app directory is read-only)
if os.environ.get('STREAMLIT_SHARING_MODE') or not os.access(DB_PATH.parent, os.W_OK):
    import shutil
    TMP_DB = Path("/tmp/ipl.duckdb")
    if not TMP_DB.exists() and DB_PATH.exists():
        shutil.copy(DB_PATH, TMP_DB)
    DB_PATH = TMP_DB

# Logo directory path
LOGO_DIR = Path(__file__).parent / "logos"
PLAYER_PLACEHOLDER = LOGO_DIR / "player_placeholder.png"

# IPL Team Colors
TEAM_COLORS = {
    'Chennai Super Kings': '#FFCB05',
    'Mumbai Indians': '#004BA0',
    'Royal Challengers Bengaluru': '#EC1C24',
    'Royal Challengers Bangalore': '#EC1C24',
    'Kolkata Knight Riders': '#3A225D',
    'Delhi Capitals': '#004C93',
    'Delhi Daredevils': '#004C93',
    'Punjab Kings': '#DD1F2D',
    'Kings XI Punjab': '#DD1F2D',
    'Rajasthan Royals': '#EA1A85',
    'Sunrisers Hyderabad': '#F7A721',
    'Gujarat Titans': '#0B4973',
    'Lucknow Super Giants': '#00A9E0',
    'Deccan Chargers': '#D5A239',
    'Pune Warriors': '#2F9BE3',
    'Gujarat Lions': '#E04F16',
    'Rising Pune Supergiant': '#6F61A0',
    'Rising Pune Supergiants': '#6F61A0',
    'Kochi Tuskers Kerala': '#FF6B00',
}

@st.cache_resource
def get_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

def run_query(query: str) -> pd.DataFrame:
    conn = get_connection()
    return conn.execute(query).fetchdf()

def get_team_logo_path(team_name):
    """Get local path for team logo."""
    if not team_name:
        return None
    filename = team_name.lower().replace(' ', '_') + '.png'
    logo_path = LOGO_DIR / filename
    if logo_path.exists():
        return str(logo_path)
    return None

def display_team_logo(team_name, size=80):
    """Display team logo with proper sizing using HTML/CSS to prevent distortion."""
    logo_path = get_team_logo_path(team_name)
    if logo_path:
        import base64
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{data}" style="max-width:{size}px; max-height:{size}px; object-fit:contain;">',
            unsafe_allow_html=True
        )

@st.cache_data(ttl=3600)
def check_image_exists(url):
    """Check if image URL returns valid response with actual image content."""
    try:
        resp = requests.head(url, timeout=2, allow_redirects=True)
        if resp.status_code != 200:
            return False
        # Check content-type is an image
        content_type = resp.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return False
        # Check content-length is reasonable (more than 1KB for a real photo)
        content_length = resp.headers.get('content-length', '0')
        if int(content_length) < 1000:
            return False
        return True
    except (requests.RequestException, requests.Timeout, ValueError):
        return False

def display_player_image(photo_url, cricinfo_id, size=100):
    """Display player image with consistent sizing using HTML/CSS."""
    import base64
    show_placeholder = True

    if photo_url and pd.notna(cricinfo_id):
        if check_image_exists(photo_url):
            st.markdown(
                f'<img src="{photo_url}" style="width:{size}px; height:{size}px; object-fit:cover; border-radius:8px;">',
                unsafe_allow_html=True
            )
            show_placeholder = False

    if show_placeholder and PLAYER_PLACEHOLDER.exists():
        with open(PLAYER_PLACEHOLDER, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{data}" style="width:{size}px; height:{size}px; object-fit:cover; border-radius:8px;">',
            unsafe_allow_html=True
        )

def display_player_cards(df, name_col, stat_col, stat_label, limit=5):
    """Display player cards with photos."""
    cols = st.columns(limit)
    for i, (idx, row) in enumerate(df.head(limit).iterrows()):
        with cols[i]:
            photo_url = row.get('photo_url')
            cricinfo_id = row.get('key_cricinfo')
            display_player_image(photo_url, cricinfo_id, size=100)
            st.markdown(f"**{row[name_col]}**")
            val = row[stat_col]
            if isinstance(val, (int, float)):
                st.metric(stat_label, f"{int(val):,}")
            else:
                st.metric(stat_label, val)

def setup_page(title="IPL Data Explorer", icon="🏏"):
    """Common page setup."""
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout="wide"
    )
    # Custom CSS for consistent image sizing
    st.markdown("""
    <style>
    /* Fix for st.image to have consistent sizing */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
    }
    [data-testid="stImage"] img {
        width: 100px !important;
        height: 100px !important;
        object-fit: cover;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)
