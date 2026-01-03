"""Cricket Data Explorer - Player vs Team comparison."""

import streamlit as st
import pandas as pd
from config import get_team_replacement_sql
from utils import run_query, display_team_logo, display_player_image


st.title("⚔️ Player vs Team")
st.caption("How a player performs against a specific team")

team_sql = get_team_replacement_sql("team")
team1_sql = get_team_replacement_sql("team1")
team2_sql = get_team_replacement_sql("team2")
batting_team_sql = get_team_replacement_sql("batting_team")

col1, col2 = st.columns(2)

with col1:
    players_t = run_query("""
        SELECT batter FROM batting_metrics
        WHERE total_runs >= 100
        ORDER BY matches DESC
    """)
    selected_player_t = st.selectbox("Select Player", players_t['batter'].tolist())

with col2:
    teams_t = run_query(f"""
        SELECT {team_sql} as team
        FROM team_metrics
        ORDER BY matches_played DESC
    """)
    selected_team_t = st.selectbox("Select Opposition Team", teams_t['team'].tolist())

if selected_player_t and selected_team_t:
    player_info = run_query(f"""
        SELECT COALESCE(p.espn_id, p.key_cricinfo) as cricinfo_id
        FROM people p
        WHERE p.name = '{selected_player_t}'
    """)

    col1, col2, col3 = st.columns([2, 1, 2])
    with col1:
        cricinfo_id = player_info['cricinfo_id'].iloc[0] if len(player_info) > 0 else None
        photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(cricinfo_id)}.png" if pd.notna(cricinfo_id) else None
        display_player_image(photo_url, cricinfo_id, size=100)
        st.markdown(f"**{selected_player_t}**")

    with col2:
        st.markdown("<div style='display:flex; align-items:center; justify-content:center; height:100px; font-size:24px;'>vs</div>", unsafe_allow_html=True)

    with col3:
        display_team_logo(selected_team_t, size=100)
        st.markdown(f"**{selected_team_t}**")

    st.divider()

    # Batting stats vs team (normalize team names for comparison)
    st.subheader("Batting Performance")
    batting_vs_team = run_query(f"""
        SELECT
            COUNT(DISTINCT d.match_id) as matches,
            SUM(CASE WHEN d.batter = '{selected_player_t}' THEN d.batter_runs ELSE 0 END) as runs,
            COUNT(CASE WHEN d.batter = '{selected_player_t}' AND (d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%') THEN 1 END) as balls,
            SUM(CASE WHEN d.batter = '{selected_player_t}' AND d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN d.batter = '{selected_player_t}' AND d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(CASE WHEN d.batter = '{selected_player_t}' AND d.is_wicket AND d.wicket_player_out = d.batter THEN 1 ELSE 0 END) as dismissals
        FROM stg_deliveries d
        JOIN stg_matches m ON d.match_id = m.match_id
        WHERE d.batter = '{selected_player_t}'
          AND {batting_team_sql} != '{selected_team_t}'
          AND ({team1_sql} = '{selected_team_t}'
               OR {team2_sql} = '{selected_team_t}')
    """)

    if len(batting_vs_team) > 0 and batting_vs_team['balls'].iloc[0] > 0:
        b = batting_vs_team.iloc[0]
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
    else:
        st.info(f"No batting data found for {selected_player_t} vs {selected_team_t}")
