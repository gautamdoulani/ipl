"""WPL Data Explorer - Player vs Player (Batter vs Bowler) comparison."""

import streamlit as st
from utils import run_query, display_player_image


st.title("⚔️ Player vs Player")
st.caption("Batter vs Bowler matchups")

# Get list of batters and bowlers (ordered by balls faced/bowled)
batters = run_query("""
    SELECT batter FROM batting_metrics
    WHERE total_runs >= 50
    ORDER BY total_balls DESC
""")
bowlers = run_query("""
    SELECT bowler FROM bowling_metrics
    WHERE total_wickets >= 5
    ORDER BY total_balls DESC
""")

col1, col2 = st.columns(2)
with col1:
    player1 = st.selectbox("Select Batter", batters['batter'].tolist(), key="pvp_batter_select")
with col2:
    player2 = st.selectbox("Select Bowler", bowlers['bowler'].tolist(), key="pvp_bowler_select")

if player1 and player2:
    # Get head-to-head stats
    h2h_stats = run_query(f"""
        SELECT
            COUNT(*) as balls_faced,
            SUM(batter_runs) as runs_scored,
            SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
            SUM(CASE WHEN batter_runs = 0 AND (extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%')) THEN 1 ELSE 0 END) as dot_balls,
            SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END) as dismissals,
            COUNT(DISTINCT match_id) as matches
        FROM stg_deliveries
        WHERE batter = '{player1}' AND bowler = '{player2}'
          AND (extras_type IS NULL OR extras_type NOT LIKE '%wides%')
    """)

    if h2h_stats['balls_faced'].iloc[0] > 0:
        stats = h2h_stats.iloc[0]

        # Display player cards
        card_col1, card_col2 = st.columns(2)

        with card_col1:
            batter_info = run_query(f"""
                SELECT b.batter, p.espn_id,
                       'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.espn_id || '.png' as photo_url
                FROM batting_metrics b
                LEFT JOIN people p ON b.batter = p.name
                WHERE b.batter = '{player1}'
            """)
            if len(batter_info) > 0:
                display_player_image(batter_info['photo_url'].iloc[0], batter_info['espn_id'].iloc[0], size=100)
            st.markdown(f"### {player1}")
            st.caption("Batter")

        with card_col2:
            bowler_info = run_query(f"""
                SELECT b.bowler, p.espn_id,
                       'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.espn_id || '.png' as photo_url
                FROM bowling_metrics b
                LEFT JOIN people p ON b.bowler = p.name
                WHERE b.bowler = '{player2}'
            """)
            if len(bowler_info) > 0:
                display_player_image(bowler_info['photo_url'].iloc[0], bowler_info['espn_id'].iloc[0], size=100)
            st.markdown(f"### {player2}")
            st.caption("Bowler")

        st.divider()

        balls = int(stats['balls_faced'])
        runs = int(stats['runs_scored'])
        dismissals = int(stats['dismissals'])

        strike_rate = round((runs / balls) * 100, 2) if balls > 0 else 0
        average = round(runs / dismissals, 2) if dismissals > 0 else runs
        dot_pct = round((stats['dot_balls'] / balls) * 100, 1) if balls > 0 else 0

        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        with stat_col1:
            st.metric("Matches", int(stats['matches']))
        with stat_col2:
            st.metric("Balls Faced", balls)
        with stat_col3:
            st.metric("Runs Scored", runs)
        with stat_col4:
            st.metric("Dismissals", dismissals)

        stat2_col1, stat2_col2, stat2_col3, stat2_col4 = st.columns(4)
        with stat2_col1:
            st.metric("Strike Rate", strike_rate)
        with stat2_col2:
            st.metric("Average", average if dismissals > 0 else "N/A")
        with stat2_col3:
            st.metric("Boundaries", f"{int(stats['fours'])} × 4, {int(stats['sixes'])} × 6")
        with stat2_col4:
            st.metric("Dot Ball %", f"{dot_pct}%")

    else:
        st.info(f"No head-to-head data found between {player1} (batting) and {player2} (bowling)")
