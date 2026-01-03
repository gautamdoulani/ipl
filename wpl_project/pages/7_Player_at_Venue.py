"""WPL Data Explorer - Player at Venue analysis."""

import streamlit as st
import pandas as pd
from utils import run_query, display_player_image


@st.cache_data
def get_players_for_venue():
    return run_query("""
        SELECT batter FROM batting_metrics
        WHERE total_runs >= 50
        ORDER BY matches DESC
    """)

@st.cache_data
def get_venues():
    return run_query("""
        SELECT venue, COUNT(*) as match_count
        FROM stg_matches
        WHERE venue IS NOT NULL
        GROUP BY venue
        ORDER BY match_count DESC
    """)


st.title("🏟️ Player at Venue")
st.caption("How a player performs at different stadiums")

col1, col2 = st.columns(2)

players_v = get_players_for_venue()
venues = get_venues()

with col1:
    selected_player_v = st.selectbox("Select Player", players_v['batter'].tolist(), key="venue_player")

with col2:
    selected_venue = st.selectbox("Select Venue", venues['venue'].tolist(), key="venue_select")

if selected_player_v and selected_venue:
    player_info = run_query(f"""
        SELECT p.espn_id
        FROM people p
        WHERE p.name = '{selected_player_v}'
    """)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        espn_id = player_info['espn_id'].iloc[0] if len(player_info) > 0 else None
        # Use ESPN ID if available for photo URL
        photo_url = None
        if pd.notna(espn_id):
            photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(espn_id)}.png"
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        display_player_image(photo_url, espn_id if photo_url else None, size=100)
        st.markdown(f"<p style='text-align:center; font-weight:bold; margin-top:8px;'>{selected_player_v}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div style='display:flex; align-items:center; justify-content:center; height:130px; font-size:24px;'>at</div>", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style='text-align:center;'>
                <div style='font-size:64px; line-height:100px;'>🏟️</div>
                <p style='font-weight:bold; margin-top:8px;'>{selected_venue}</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Batting stats at venue
    st.subheader("Batting at this Venue")
    batting_at_venue = run_query(f"""
        SELECT
            COUNT(DISTINCT d.match_id) as matches,
            SUM(d.batter_runs) as runs,
            COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%' THEN 1 END) as balls,
            SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(CASE WHEN d.is_wicket AND d.wicket_player_out = d.batter THEN 1 ELSE 0 END) as dismissals
        FROM stg_deliveries d
        JOIN stg_matches m ON d.match_id = m.match_id
        WHERE d.batter = '{selected_player_v}'
          AND m.venue = '{selected_venue}'
    """)

    if len(batting_at_venue) > 0 and batting_at_venue['balls'].iloc[0] > 0:
        b = batting_at_venue.iloc[0]
        runs = int(b['runs'])
        balls = int(b['balls'])
        dismissals = int(b['dismissals'])
        sr = round(runs * 100 / balls, 2) if balls > 0 else 0
        avg = round(runs / dismissals, 2) if dismissals > 0 else runs

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Matches", int(b['matches']))
        with col2:
            st.metric("Runs", runs)
        with col3:
            st.metric("Average", avg if dismissals > 0 else "N/A")
        with col4:
            st.metric("Strike Rate", sr)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Balls Faced", balls)
        with col2:
            st.metric("Boundaries", f"{int(b['fours'])} × 4, {int(b['sixes'])} × 6")
    else:
        st.info(f"No batting data found for {selected_player_v} at {selected_venue}")
