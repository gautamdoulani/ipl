"""IPL Data Explorer - Stadium Profile page."""

import streamlit as st
import pandas as pd
from utils import run_query


@st.cache_data
def get_venues():
    return run_query("""
        SELECT venue, COUNT(*) as match_count
        FROM stg_matches
        WHERE venue IS NOT NULL
        GROUP BY venue
        ORDER BY match_count DESC
    """)


st.title("🏟️ Stadium Profile")

venues = get_venues()
selected_venue = st.selectbox("Select Stadium", venues['venue'].tolist())

if selected_venue:
    # Stadium header
    st.markdown(f"""
        <div style='text-align:center; padding:20px;'>
            <div style='font-size:72px;'>🏟️</div>
            <h2>{selected_venue}</h2>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Basic stats
    venue_stats = run_query(f"""
        SELECT
            COUNT(*) as total_matches,
            MIN(match_date) as first_match,
            MAX(match_date) as last_match,
            COUNT(DISTINCT season) as seasons
        FROM stg_matches
        WHERE venue = '{selected_venue}'
    """)

    if len(venue_stats) > 0:
        stats = venue_stats.iloc[0]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", int(stats['total_matches']))
        with col2:
            st.metric("Seasons", int(stats['seasons']))
        with col3:
            st.metric("First Match", str(stats['first_match'])[:10])
        with col4:
            st.metric("Last Match", str(stats['last_match'])[:10])

    st.divider()

    # Tabs for different stats
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Match Stats", "🏏 Top Batters", "🎳 Top Bowlers", "🏆 Teams"])

    with tab1:
        # Batting first vs chasing stats
        toss_stats = run_query(f"""
            SELECT
                COUNT(*) as matches,
                SUM(CASE WHEN toss_decision = 'bat' THEN 1 ELSE 0 END) as chose_bat,
                SUM(CASE WHEN toss_decision = 'field' THEN 1 ELSE 0 END) as chose_field,
                SUM(CASE WHEN (toss_decision = 'bat' AND toss_winner = winner)
                           OR (toss_decision = 'field' AND toss_winner != winner AND winner IS NOT NULL) THEN 1 ELSE 0 END) as batting_first_wins,
                SUM(CASE WHEN (toss_decision = 'field' AND toss_winner = winner)
                           OR (toss_decision = 'bat' AND toss_winner != winner AND winner IS NOT NULL) THEN 1 ELSE 0 END) as chasing_wins
            FROM stg_matches
            WHERE venue = '{selected_venue}' AND winner IS NOT NULL
        """)

        if len(toss_stats) > 0:
            ts = toss_stats.iloc[0]
            total = int(ts['matches'])
            bat_first_wins = int(ts['batting_first_wins'])
            chase_wins = int(ts['chasing_wins'])

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Batting First Wins", bat_first_wins)
            with col2:
                st.metric("Chasing Wins", chase_wins)
            with col3:
                if total > 0:
                    chase_pct = round(chase_wins * 100 / total, 1)
                    st.metric("Chase Win %", f"{chase_pct}%")

        # Average scores
        st.subheader("Average Scores")
        avg_scores = run_query(f"""
            WITH innings_totals AS (
                SELECT
                    d.match_id,
                    d.innings,
                    SUM(d.total_runs) as total
                FROM stg_deliveries d
                JOIN stg_matches m ON d.match_id = m.match_id
                WHERE m.venue = '{selected_venue}'
                GROUP BY d.match_id, d.innings
            )
            SELECT
                ROUND(AVG(CASE WHEN innings = 1 THEN total END), 0) as avg_first_innings,
                ROUND(AVG(CASE WHEN innings = 2 THEN total END), 0) as avg_second_innings,
                MAX(total) as highest_total,
                MIN(total) as lowest_total
            FROM innings_totals
        """)

        if len(avg_scores) > 0:
            avs = avg_scores.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Avg 1st Innings", int(avs['avg_first_innings']) if pd.notna(avs['avg_first_innings']) else "N/A")
            with col2:
                st.metric("Avg 2nd Innings", int(avs['avg_second_innings']) if pd.notna(avs['avg_second_innings']) else "N/A")
            with col3:
                st.metric("Highest Total", int(avs['highest_total']) if pd.notna(avs['highest_total']) else "N/A")
            with col4:
                st.metric("Lowest Total", int(avs['lowest_total']) if pd.notna(avs['lowest_total']) else "N/A")

    with tab2:
        # Top run scorers at venue
        st.subheader("Top Run Scorers")
        top_batters = run_query(f"""
            SELECT
                d.batter,
                COUNT(DISTINCT d.match_id) as matches,
                SUM(d.batter_runs) as runs,
                COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%' THEN 1 END) as balls,
                SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
                SUM(CASE WHEN d.is_wicket AND d.wicket_player_out = d.batter THEN 1 ELSE 0 END) as dismissals,
                ROUND(SUM(d.batter_runs) * 100.0 / NULLIF(COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%' THEN 1 END), 0), 2) as strike_rate,
                ROUND(SUM(d.batter_runs) * 1.0 / NULLIF(SUM(CASE WHEN d.is_wicket AND d.wicket_player_out = d.batter THEN 1 ELSE 0 END), 0), 2) as average
            FROM stg_deliveries d
            JOIN stg_matches m ON d.match_id = m.match_id
            WHERE m.venue = '{selected_venue}'
            GROUP BY d.batter
            HAVING SUM(d.batter_runs) >= 100
            ORDER BY runs DESC
            LIMIT 20
        """)

        if len(top_batters) > 0:
            st.dataframe(top_batters, use_container_width=True, hide_index=True)
        else:
            st.info("No batting data available for this venue")

    with tab3:
        # Top wicket takers at venue
        st.subheader("Top Wicket Takers")
        top_bowlers = run_query(f"""
            SELECT
                d.bowler,
                COUNT(DISTINCT d.match_id) as matches,
                COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT IN ('wides', 'noballs') THEN 1 END) as balls,
                SUM(d.total_runs) as runs,
                SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) as wickets,
                ROUND(SUM(d.total_runs) * 6.0 / NULLIF(COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT IN ('wides', 'noballs') THEN 1 END), 0), 2) as economy,
                ROUND(SUM(d.total_runs) * 1.0 / NULLIF(SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END), 0), 2) as average
            FROM stg_deliveries d
            JOIN stg_matches m ON d.match_id = m.match_id
            WHERE m.venue = '{selected_venue}'
            GROUP BY d.bowler
            HAVING SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) >= 5
            ORDER BY wickets DESC
            LIMIT 20
        """)

        if len(top_bowlers) > 0:
            st.dataframe(top_bowlers, use_container_width=True, hide_index=True)
        else:
            st.info("No bowling data available for this venue")

    with tab4:
        # Team records at venue
        st.subheader("Team Records")
        team_records = run_query(f"""
            WITH team_matches AS (
                SELECT team, match_id, winner
                FROM (
                    SELECT team1 as team, match_id, winner FROM stg_matches WHERE venue = '{selected_venue}'
                    UNION ALL
                    SELECT team2 as team, match_id, winner FROM stg_matches WHERE venue = '{selected_venue}'
                )
            )
            SELECT
                team,
                COUNT(*) as matches,
                SUM(CASE WHEN team = winner THEN 1 ELSE 0 END) as wins,
                ROUND(SUM(CASE WHEN team = winner THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as win_pct
            FROM team_matches
            GROUP BY team
            HAVING COUNT(*) >= 3
            ORDER BY wins DESC, win_pct DESC
        """)

        if len(team_records) > 0:
            st.dataframe(team_records, use_container_width=True, hide_index=True)
        else:
            st.info("No team data available for this venue")

        # Recent matches
        st.subheader("Recent Matches")
        recent = run_query(f"""
            SELECT
                match_date,
                team1,
                team2,
                winner,
                CASE
                    WHEN win_by_runs > 0 THEN win_by_runs || ' runs'
                    WHEN win_by_wickets > 0 THEN win_by_wickets || ' wickets'
                    ELSE 'N/A'
                END as margin,
                player_of_match
            FROM stg_matches
            WHERE venue = '{selected_venue}'
            ORDER BY match_date DESC
            LIMIT 10
        """)

        if len(recent) > 0:
            st.dataframe(recent, use_container_width=True, hide_index=True)
