"""IPL Data Explorer - Player at Venue analysis."""

import streamlit as st
import pandas as pd
from utils import run_query, display_player_image


st.title("🏟️ Player at Venue")
st.caption("How a player performs at different stadiums")

col1, col2 = st.columns(2)

with col1:
    players_v = run_query("""
        SELECT DISTINCT batter FROM batting_metrics
        WHERE total_runs >= 100
        ORDER BY batter
    """)
    selected_player_v = st.selectbox("Select Player", players_v['batter'].tolist())

with col2:
    venues = run_query("""
        SELECT DISTINCT venue FROM stg_matches
        WHERE venue IS NOT NULL
        ORDER BY venue
    """)
    selected_venue = st.selectbox("Select Venue", venues['venue'].tolist())

if selected_player_v and selected_venue:
    player_info = run_query(f"""
        SELECT b.cricinfo_id
        FROM batting_metrics b
        WHERE b.batter = '{selected_player_v}'
    """)

    col1, col2 = st.columns([1, 3])
    with col1:
        cricinfo_id = player_info['cricinfo_id'].iloc[0] if len(player_info) > 0 else None
        photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(cricinfo_id)}.png" if pd.notna(cricinfo_id) else None
        display_player_image(photo_url, cricinfo_id, size=100)

    with col2:
        st.markdown(f"### {selected_player_v}")
        st.caption(f"at {selected_venue}")

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
