"""IPL Data Explorer - Impact Players analysis."""

import streamlit as st
import pandas as pd
from utils import run_query, display_player_image


st.title("⭐ Impact Players")
st.info("**Impact Player Rule (2023+):** Each team can substitute one player from their playing XI with a player from the bench at any point before the completion of the 14th over of either innings.")

# Usage Patterns Section
st.subheader("📊 Usage Patterns")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**Innings Distribution**")
    innings_dist = run_query("""
        SELECT
            d.innings as "Innings",
            COUNT(DISTINCT ip.match_id || '-' || ip.player_in) as "Times Used"
        FROM impact_players ip
        JOIN stg_deliveries d ON ip.match_id = d.match_id AND ip.player_in = d.batter
        GROUP BY d.innings
        ORDER BY d.innings
    """)
    if len(innings_dist) > 0:
        total = innings_dist['Times Used'].sum()
        for _, row in innings_dist.iterrows():
            pct = round(row['Times Used'] * 100 / total, 1)
            inn_label = "1st Innings" if row['Innings'] == 1 else "2nd Innings"
            st.metric(inn_label, f"{row['Times Used']} ({pct}%)")

with col2:
    st.markdown("**What They Did**")
    role_dist = run_query("""
        WITH roles AS (
            SELECT
                ip.match_id,
                ip.player_in,
                MAX(CASE WHEN d.batter = ip.player_in THEN 1 ELSE 0 END) as batted,
                MAX(CASE WHEN d.bowler = ip.player_in THEN 1 ELSE 0 END) as bowled
            FROM impact_players ip
            LEFT JOIN stg_deliveries d ON ip.match_id = d.match_id
                AND (ip.player_in = d.batter OR ip.player_in = d.bowler)
            GROUP BY ip.match_id, ip.player_in
        )
        SELECT
            CASE
                WHEN batted = 1 AND bowled = 1 THEN 'Both'
                WHEN batted = 1 THEN 'Batter'
                WHEN bowled = 1 THEN 'Bowler'
                ELSE 'Did Not Play'
            END as role,
            COUNT(*) as times
        FROM roles
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    for _, row in role_dist.iterrows():
        st.metric(row['role'], row['times'])

with col3:
    st.markdown("**When Batting Starts**")
    phase_bat = run_query("""
        WITH first_appearance AS (
            SELECT
                ip.match_id,
                ip.player_in,
                MIN(d.over_number) as first_over
            FROM impact_players ip
            JOIN stg_deliveries d ON ip.match_id = d.match_id AND ip.player_in = d.batter
            GROUP BY ip.match_id, ip.player_in
        )
        SELECT
            CASE
                WHEN first_over <= 5 THEN 'Powerplay (1-6)'
                WHEN first_over <= 14 THEN 'Middle (7-15)'
                ELSE 'Death (16-20)'
            END as phase,
            COUNT(*) as times
        FROM first_appearance
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    for _, row in phase_bat.iterrows():
        st.metric(row['phase'], row['times'])

with col4:
    st.markdown("**When Bowling Starts**")
    phase_bowl = run_query("""
        WITH first_bowl AS (
            SELECT
                ip.match_id,
                ip.player_in,
                MIN(d.over_number) as first_over
            FROM impact_players ip
            JOIN stg_deliveries d ON ip.match_id = d.match_id AND ip.player_in = d.bowler
            GROUP BY ip.match_id, ip.player_in
        )
        SELECT
            CASE
                WHEN first_over <= 5 THEN 'Powerplay (1-6)'
                WHEN first_over <= 14 THEN 'Middle (7-15)'
                ELSE 'Death (16-20)'
            END as phase,
            COUNT(*) as times
        FROM first_bowl
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    for _, row in phase_bowl.iterrows():
        st.metric(row['phase'], row['times'])

st.divider()

st.subheader("Most Used as Impact Player (Coming In)")

# Get top 5 with photos
top5_impact = run_query("""
    SELECT
        ip.player_in as player,
        COUNT(*) as times_used,
        p.key_cricinfo
    FROM impact_players ip
    LEFT JOIN people p ON ip.player_in = p.name
    GROUP BY ip.player_in, p.key_cricinfo
    ORDER BY times_used DESC
    LIMIT 5
""")

# Display top 5 with photos
cols = st.columns(5)
for i, (_, row) in enumerate(top5_impact.iterrows()):
    with cols[i]:
        cricinfo_id = row['key_cricinfo']
        photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(cricinfo_id)}.png" if pd.notna(cricinfo_id) else None
        display_player_image(photo_url, cricinfo_id, size=80)
        st.markdown(f"**{row['player']}**")
        st.caption(f"{int(row['times_used'])} times")

st.markdown("---")

# Full table
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

# Get top 5 replaced with photos
top5_replaced = run_query("""
    SELECT
        ip.player_out as player,
        COUNT(*) as times_replaced,
        p.key_cricinfo
    FROM impact_players ip
    LEFT JOIN people p ON ip.player_out = p.name
    GROUP BY ip.player_out, p.key_cricinfo
    ORDER BY times_replaced DESC
    LIMIT 5
""")

# Display top 5 with photos
cols = st.columns(5)
for i, (_, row) in enumerate(top5_replaced.iterrows()):
    with cols[i]:
        cricinfo_id = row['key_cricinfo']
        photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(cricinfo_id)}.png" if pd.notna(cricinfo_id) else None
        display_player_image(photo_url, cricinfo_id, size=80)
        st.markdown(f"**{row['player']}**")
        st.caption(f"{int(row['times_replaced'])} times")

st.markdown("---")

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
