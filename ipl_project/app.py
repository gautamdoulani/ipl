#!/usr/bin/env python3
"""IPL Data Explorer - Multi-page Streamlit App."""

import streamlit as st

# Page config - must be first Streamlit command
st.set_page_config(
    page_title="IPL Data Explorer",
    page_icon="🏏",
    layout="wide"
)

# Define pages with custom names
overview = st.Page("pages/0_Overview.py", title="Overview", icon="🏏", default=True)
batting = st.Page("pages/1_Batting_Stats.py", title="Batting Stats", icon="🏏")
bowling = st.Page("pages/2_Bowling_Stats.py", title="Bowling Stats", icon="🎳")
player_profile = st.Page("pages/11_Player_Profile.py", title="Player Profile", icon="👤")
match_analysis = st.Page("pages/3_Match_Analysis.py", title="Match Analysis", icon="📊")
stadium_profile = st.Page("pages/12_Stadium_Profile.py", title="Stadium Profile", icon="🏟️")
team_vs_team = st.Page("pages/4_Team_vs_Team.py", title="Team vs Team", icon="⚔️")
player_vs_player = st.Page("pages/5_Player_vs_Player.py", title="Player vs Player", icon="⚔️")
player_vs_team = st.Page("pages/6_Player_vs_Team.py", title="Player vs Team", icon="⚔️")
player_at_venue = st.Page("pages/7_Player_at_Venue.py", title="Player at Venue", icon="🏟️")
impact_players = st.Page("pages/8_Impact_Players.py", title="Impact Players", icon="⭐")
sql_query = st.Page("pages/9_SQL_Query.py", title="SQL Query", icon="🔍")
credits = st.Page("pages/13_Credits.py", title="Credits", icon="🙏")

# Build navigation
pg = st.navigation({
    "Home": [overview],
    "Player Stats": [batting, bowling, player_profile],
    "Match & Venue": [match_analysis, stadium_profile],
    "Head to Head": [team_vs_team, player_vs_player, player_vs_team, player_at_venue],
    "Other": [impact_players, sql_query, credits]
})

# Run the selected page
pg.run()
