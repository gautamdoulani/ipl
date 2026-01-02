"""IPL Data Explorer - Player Profile page."""

import streamlit as st
import pandas as pd
from utils import run_query, display_player_image


@st.cache_data
def get_all_players():
    return run_query("""
        WITH player_balls AS (
            SELECT
                batter as name,
                batter_cricinfo_id as key_cricinfo,
                COUNT(*) as balls
            FROM stg_deliveries
            WHERE batter IS NOT NULL
            GROUP BY batter, batter_cricinfo_id

            UNION ALL

            SELECT
                bowler as name,
                bowler_cricinfo_id as key_cricinfo,
                COUNT(*) as balls
            FROM stg_deliveries
            WHERE bowler IS NOT NULL
            GROUP BY bowler, bowler_cricinfo_id
        )
        SELECT name, key_cricinfo, SUM(balls) as total_balls
        FROM player_balls
        GROUP BY name, key_cricinfo
        ORDER BY total_balls DESC
    """)


st.title("👤 Player Profile")

players = get_all_players()

selected_player = st.selectbox("Select Player", players['name'].tolist(), key="player_profile_select")

if selected_player:
    # Get player's cricinfo ID
    player_info = players[players['name'] == selected_player].iloc[0]
    cricinfo_id = player_info['key_cricinfo']

    # Player header with photo
    col1, col2 = st.columns([1, 4])
    with col1:
        photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(cricinfo_id)}.png" if pd.notna(cricinfo_id) else None
        display_player_image(photo_url, cricinfo_id, size=120)

    with col2:
        st.markdown(f"## {selected_player}")

    st.divider()

    # Career stats tabs
    tab1, tab2 = st.tabs(["🏏 Batting", "🎳 Bowling"])

    with tab1:
        # Batting stats
        batting_stats = run_query(f"""
            WITH batting_agg AS (
                SELECT
                    COUNT(DISTINCT match_id) as matches,
                    COUNT(DISTINCT match_id || '-' || innings) as innings,
                    SUM(batter_runs) as runs,
                    COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) as balls,
                    SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as fours,
                    SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
                    SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END) as dismissals
                FROM stg_deliveries
                WHERE batter = '{selected_player}'
            ),
            innings_scores AS (
                SELECT match_id, innings, SUM(batter_runs) as score
                FROM stg_deliveries
                WHERE batter = '{selected_player}'
                GROUP BY match_id, innings
            )
            SELECT
                b.*,
                (SELECT MAX(score) FROM innings_scores) as highest,
                (SELECT COUNT(*) FROM innings_scores WHERE score >= 50 AND score < 100) as fifties,
                (SELECT COUNT(*) FROM innings_scores WHERE score >= 100) as centuries
            FROM batting_agg b
        """)

        if len(batting_stats) > 0 and batting_stats['balls'].iloc[0] > 0:
            stats = batting_stats.iloc[0]
            runs = int(stats['runs'])
            balls = int(stats['balls'])
            dismissals = int(stats['dismissals'])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Matches", int(stats['matches']))
            with col2:
                st.metric("Innings", int(stats['innings']))
            with col3:
                st.metric("Runs", f"{runs:,}")
            with col4:
                st.metric("Highest", int(stats['highest']))

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg = round(runs / dismissals, 2) if dismissals > 0 else runs
                st.metric("Average", avg if dismissals > 0 else "N/A")
            with col2:
                sr = round(runs * 100 / balls, 2) if balls > 0 else 0
                st.metric("Strike Rate", sr)
            with col3:
                st.metric("50s / 100s", f"{int(stats['fifties'])} / {int(stats['centuries'])}")
            with col4:
                st.metric("4s / 6s", f"{int(stats['fours'])} / {int(stats['sixes'])}")

            st.markdown("---")

            # Top 10 bowlers faced
            st.subheader("Most Faced Bowlers")
            bowlers_faced = run_query(f"""
                SELECT
                    bowler,
                    COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) as balls,
                    SUM(batter_runs) as runs,
                    SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as "4s",
                    SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as "6s",
                    SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END) as dismissals,
                    ROUND(SUM(batter_runs) * 1.0 / NULLIF(SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END), 0), 2) as average,
                    ROUND(SUM(batter_runs) * 100.0 / NULLIF(COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END), 0), 2) as strike_rate
                FROM stg_deliveries
                WHERE batter = '{selected_player}'
                GROUP BY bowler
                ORDER BY balls DESC
                LIMIT 50
            """)
            if len(bowlers_faced) > 0:
                st.dataframe(bowlers_faced, use_container_width=True, hide_index=True)
        else:
            st.info(f"No batting data found for {selected_player}")

    with tab2:
        # Bowling stats with wicket hauls
        bowling_stats = run_query(f"""
            WITH bowling_innings AS (
                SELECT
                    match_id,
                    SUM(total_runs) as runs_conceded,
                    COUNT(*) as balls,
                    SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) as wickets
                FROM stg_deliveries
                WHERE bowler = '{selected_player}'
                GROUP BY match_id
            ),
            best_figures AS (
                SELECT wickets, runs_conceded
                FROM bowling_innings
                ORDER BY wickets DESC, runs_conceded ASC
                LIMIT 1
            )
            SELECT
                COUNT(DISTINCT match_id) as matches,
                SUM(balls) as balls,
                SUM(runs_conceded) as runs_conceded,
                SUM(wickets) as wickets,
                SUM(CASE WHEN wickets = 4 THEN 1 ELSE 0 END) as four_wickets,
                SUM(CASE WHEN wickets >= 5 THEN 1 ELSE 0 END) as five_wickets,
                (SELECT wickets || '/' || runs_conceded FROM best_figures) as best_bowling
            FROM bowling_innings
        """)

        if len(bowling_stats) > 0 and bowling_stats['balls'].iloc[0] > 0:
            stats = bowling_stats.iloc[0]
            balls = int(stats['balls'])
            runs = int(stats['runs_conceded'])
            wickets = int(stats['wickets'])

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Matches", int(stats['matches']))
            with col2:
                overs = f"{balls // 6}.{balls % 6}"
                st.metric("Overs", overs)
            with col3:
                st.metric("Wickets", wickets)
            with col4:
                st.metric("Best Bowling", stats['best_bowling'] if stats['best_bowling'] else "N/A")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                avg = round(runs / wickets, 2) if wickets > 0 else "N/A"
                st.metric("Average", avg)
            with col2:
                econ = round(runs * 6 / balls, 2) if balls > 0 else 0
                st.metric("Economy", econ)
            with col3:
                sr = round(balls / wickets, 2) if wickets > 0 else "N/A"
                st.metric("Strike Rate", sr)
            with col4:
                st.metric("4W / 5W", f"{int(stats['four_wickets'])} / {int(stats['five_wickets'])}")

            st.markdown("---")

            # Top 10 batsmen bowled to
            st.subheader("Most Bowled To Batsmen")
            batsmen_bowled = run_query(f"""
                SELECT
                    batter,
                    COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) as balls,
                    SUM(batter_runs) as runs,
                    SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as "4s",
                    SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as "6s",
                    SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) as wickets,
                    ROUND(SUM(total_runs) * 1.0 / NULLIF(SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END), 0), 2) as average,
                    ROUND(COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) * 1.0 / NULLIF(SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END), 0), 2) as strike_rate,
                    ROUND(SUM(total_runs) * 6.0 / NULLIF(COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END), 0), 2) as economy
                FROM stg_deliveries
                WHERE bowler = '{selected_player}'
                GROUP BY batter
                ORDER BY balls DESC
                LIMIT 50
            """)
            if len(batsmen_bowled) > 0:
                st.dataframe(batsmen_bowled, use_container_width=True, hide_index=True)
        else:
            st.info(f"No bowling data found for {selected_player}")
