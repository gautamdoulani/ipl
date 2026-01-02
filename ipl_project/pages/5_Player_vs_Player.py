"""IPL Data Explorer - Player vs Player (Batter vs Bowler) comparison."""

import streamlit as st
import pandas as pd
from utils import run_query, display_player_image


st.title("⚔️ Player vs Player")
st.caption("Batter vs Bowler matchups")

# Get list of batters and bowlers
batters = run_query("""
    SELECT DISTINCT batter FROM batting_metrics
    WHERE total_runs >= 100
    ORDER BY batter
""")
bowlers = run_query("""
    SELECT DISTINCT bowler FROM bowling_metrics
    WHERE total_wickets >= 10
    ORDER BY bowler
""")

col1, col2 = st.columns(2)
with col1:
    player1 = st.selectbox("Select Batter", batters['batter'].tolist())
with col2:
    player2 = st.selectbox("Select Bowler", bowlers['bowler'].tolist())

if player1 and player2:
    # Get head-to-head stats
    h2h_stats = run_query(f"""
        SELECT
            COUNT(*) as balls_faced,
            SUM(batter_runs) as runs_scored,
            SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(CASE WHEN batter_runs = 0 AND (extras_type IS NULL OR extras_type NOT IN ('wides', 'noballs')) THEN 1 ELSE 0 END) as dot_balls,
            SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END) as dismissals,
            COUNT(DISTINCT match_id) as matches
        FROM stg_deliveries
        WHERE batter = '{player1}' AND bowler = '{player2}'
          AND (extras_type IS NULL OR extras_type NOT LIKE '%wides%')
    """)

    if h2h_stats['balls_faced'].iloc[0] > 0:
        stats = h2h_stats.iloc[0]

        # Display player cards
        col1, col2 = st.columns(2)

        with col1:
            batter_info = run_query(f"""
                SELECT b.batter, p.key_cricinfo,
                       'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.key_cricinfo || '.png' as photo_url
                FROM batting_metrics b
                LEFT JOIN people p ON b.batter = p.name
                WHERE b.batter = '{player1}'
            """)
            if len(batter_info) > 0:
                display_player_image(batter_info['photo_url'].iloc[0], batter_info['key_cricinfo'].iloc[0], size=100)
            st.markdown(f"### {player1}")
            st.caption("Batter")

        with col2:
            bowler_info = run_query(f"""
                SELECT b.bowler, p.key_cricinfo,
                       'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.key_cricinfo || '.png' as photo_url
                FROM bowling_metrics b
                LEFT JOIN people p ON b.bowler = p.name
                WHERE b.bowler = '{player2}'
            """)
            if len(bowler_info) > 0:
                display_player_image(bowler_info['photo_url'].iloc[0], bowler_info['key_cricinfo'].iloc[0], size=100)
            st.markdown(f"### {player2}")
            st.caption("Bowler")

        st.divider()

        balls = int(stats['balls_faced'])
        runs = int(stats['runs_scored'])
        dismissals = int(stats['dismissals'])

        strike_rate = round((runs / balls) * 100, 2) if balls > 0 else 0
        average = round(runs / dismissals, 2) if dismissals > 0 else runs
        dot_pct = round((stats['dot_balls'] / balls) * 100, 1) if balls > 0 else 0

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Matches", int(stats['matches']))
        with col2:
            st.metric("Balls Faced", balls)
        with col3:
            st.metric("Runs Scored", runs)
        with col4:
            st.metric("Dismissals", dismissals)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Strike Rate", strike_rate)
        with col2:
            st.metric("Average", average if dismissals > 0 else "N/A")
        with col3:
            st.metric("Boundaries", f"{int(stats['fours'])} × 4, {int(stats['sixes'])} × 6")
        with col4:
            st.metric("Dot Ball %", f"{dot_pct}%")

    else:
        st.info(f"No head-to-head data found between {player1} (batting) and {player2} (bowling)")
