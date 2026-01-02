"""IPL Data Explorer - Impact Players analysis."""

import streamlit as st
from utils import run_query


st.title("⭐ Impact Players")
st.info("**Impact Player Rule (2023+):** Each team can substitute one player from their playing XI with a player from the bench at any point before the completion of the 14th over of either innings.")

st.subheader("Most Used as Impact Player (Coming In)")
most_used_in = run_query("""
    SELECT
        player_in as player,
        COUNT(*) as times_used,
        COUNT(DISTINCT REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant')) as teams,
        STRING_AGG(DISTINCT season, ', ' ORDER BY season) as seasons
    FROM impact_players
    GROUP BY player_in
    ORDER BY times_used DESC
    LIMIT 20
""")
st.dataframe(most_used_in, use_container_width=True, hide_index=True)

st.subheader("Most Replaced (Going Out)")
most_replaced = run_query("""
    SELECT
        player_out as player,
        COUNT(*) as times_replaced,
        COUNT(DISTINCT REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant')) as teams,
        STRING_AGG(DISTINCT season, ', ' ORDER BY season) as seasons
    FROM impact_players
    GROUP BY player_out
    ORDER BY times_replaced DESC
    LIMIT 20
""")
st.dataframe(most_replaced, use_container_width=True, hide_index=True)

st.subheader("Impact Players by Team")
team_impact = run_query("""
    SELECT
        REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team,
        season,
        COUNT(*) as substitutions,
        COUNT(DISTINCT player_in) as unique_players_in
    FROM impact_players
    GROUP BY REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant'), season
    ORDER BY season DESC, substitutions DESC
""")
st.dataframe(team_impact, use_container_width=True, hide_index=True)

st.subheader("Recent Impact Player Substitutions")
recent_subs = run_query("""
    SELECT
        ip.season,
        REPLACE(REPLACE(ip.team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team,
        ip.player_in as "Player In",
        ip.player_out as "Player Out",
        m.match_date,
        REPLACE(REPLACE(CASE WHEN m.team1 = ip.team THEN m.team2 ELSE m.team1 END, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as opponent
    FROM impact_players ip
    JOIN stg_matches m ON ip.match_id = m.match_id
    ORDER BY m.match_date DESC
    LIMIT 30
""")
st.dataframe(recent_subs, use_container_width=True, hide_index=True)
