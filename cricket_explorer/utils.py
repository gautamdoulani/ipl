"""Shared utilities for Cricket Data Explorer app."""

import base64
import os
from pathlib import Path

import duckdb
import pandas as pd
import requests
import streamlit as st


def inject_mobile_styles():
    """Inject CSS for mobile-responsive layouts."""
    st.markdown("""
    <style>
    /* Mobile-responsive styles */
    @media (max-width: 768px) {
        /* Make dataframes scrollable with hint */
        .stDataFrame {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch;
        }

        /* Reduce padding on mobile */
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* Stack metric cards better */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }

        /* Responsive images */
        img {
            max-width: 100% !important;
            height: auto !important;
        }

        /* Better table display */
        table {
            font-size: 0.8rem !important;
        }

        /* Player cards - make text smaller */
        .player-card {
            text-align: center;
            padding: 0.5rem;
        }

        .player-card img {
            width: 60px !important;
            height: 60px !important;
        }

        /* Reduce header sizes */
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }

        /* Trophy cabinet - smaller logos */
        .trophy-item img {
            max-width: 50px !important;
            max-height: 50px !important;
        }
    }

    /* Tablet adjustments */
    @media (max-width: 1024px) and (min-width: 769px) {
        [data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }
    }

    /* Scroll hint for tables */
    .scroll-hint {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        padding: 0.5rem;
    }

    /* Responsive grid for player cards */
    .player-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
        gap: 1rem;
    }

    /* Card styling */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        color: white;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)


def get_responsive_columns(total_items, max_desktop=5, max_tablet=3, max_mobile=2):
    """Return appropriate number of columns based on content and provide column count."""
    return min(total_items, max_desktop)


# Logo directory path
LOGO_DIR = Path(__file__).parent / "logos"
PLAYER_PLACEHOLDER = LOGO_DIR / "player_placeholder.png"


def get_db_path():
    """Get database path dynamically from config."""
    from config import CONFIG
    db_path = Path(__file__).parent / "data" / CONFIG["db_file"]

    # For Streamlit Cloud, copy to tmp if needed (since app directory is read-only)
    if os.environ.get('STREAMLIT_SHARING_MODE') or not os.access(db_path.parent, os.W_OK):
        import shutil
        tmp_db = Path(f"/tmp/{CONFIG['db_file']}")
        if not tmp_db.exists() and db_path.exists():
            shutil.copy(db_path, tmp_db)
        db_path = tmp_db

    return db_path


def get_connection():
    """Get database connection (cached per database file)."""
    db_path = get_db_path()
    return duckdb.connect(str(db_path), read_only=True)


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
        content_type = resp.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return False
        content_length = resp.headers.get('content-length', '0')
        if int(content_length) < 1000:
            return False
        return True
    except (requests.RequestException, requests.Timeout, ValueError):
        return False


def display_player_image(photo_url, cricinfo_id, size=100):
    """Display player image with consistent sizing using HTML/CSS."""
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
    """Display player cards with photos - mobile responsive."""
    num_items = min(len(df), limit)
    num_cols = get_responsive_columns(num_items, max_desktop=5, max_tablet=3, max_mobile=2)
    cols = st.columns(num_cols)
    for i, (idx, row) in enumerate(df.head(limit).iterrows()):
        with cols[i % num_cols]:
            st.markdown('<div class="player-card">', unsafe_allow_html=True)
            photo_url = row.get('photo_url')
            cricinfo_id = row.get('key_cricinfo')
            display_player_image(photo_url, cricinfo_id, size=100)
            st.markdown(f"**{row[name_col]}**")
            val = row[stat_col]
            if isinstance(val, (int, float)):
                st.metric(stat_label, f"{int(val):,}")
            else:
                st.metric(stat_label, val)
            st.markdown('</div>', unsafe_allow_html=True)
