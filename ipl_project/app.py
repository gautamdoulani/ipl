#!/usr/bin/env python3
"""Streamlit app for exploring IPL cricket data."""

import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import os

# Page config
st.set_page_config(
    page_title="IPL Data Explorer",
    page_icon="🏏",
    layout="wide"
)

# Database connection - use writable path for Streamlit Cloud
DB_PATH = Path(__file__).parent / "ipl.duckdb"

# For Streamlit Cloud, copy to tmp if needed (since app directory is read-only)
if os.environ.get('STREAMLIT_SHARING_MODE') or not os.access(DB_PATH.parent, os.W_OK):
    import shutil
    TMP_DB = Path("/tmp/ipl.duckdb")
    if not TMP_DB.exists() and DB_PATH.exists():
        shutil.copy(DB_PATH, TMP_DB)
    DB_PATH = TMP_DB

@st.cache_resource
def get_connection():
    return duckdb.connect(str(DB_PATH), read_only=True)

def run_query(query: str) -> pd.DataFrame:
    conn = get_connection()
    return conn.execute(query).fetchdf()

def get_player_photo_url(cricinfo_id):
    """Generate ESPN photo URL from cricinfo ID."""
    if cricinfo_id and pd.notna(cricinfo_id):
        return f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(cricinfo_id)}.png"
    return None

def display_player_cards(df, name_col, stat_col, stat_label, limit=5):
    """Display player cards with photos."""
    cols = st.columns(limit)
    for i, (idx, row) in enumerate(df.head(limit).iterrows()):
        with cols[i]:
            photo_url = row.get('photo_url')
            if photo_url:
                st.image(photo_url, width=100)
            st.markdown(f"**{row[name_col]}**")
            st.metric(stat_label, f"{row[stat_col]:,}" if isinstance(row[stat_col], (int, float)) else row[stat_col])

# Sidebar navigation
st.sidebar.title("🏏 IPL Explorer")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "IPL Winners", "Batting Stats", "Bowling Stats", "Match Analysis", "Head to Head", "SQL Query"]
)

# Overview page
if page == "Overview":
    st.title("🏏 IPL Data Explorer")
    st.markdown("Explore IPL cricket data from 2008-2025")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        matches = run_query("SELECT COUNT(*) as cnt FROM matches")
        st.metric("Total Matches", f"{matches['cnt'].iloc[0]:,}")

    with col2:
        deliveries = run_query("SELECT COUNT(*) as cnt FROM deliveries")
        st.metric("Total Deliveries", f"{deliveries['cnt'].iloc[0]:,}")

    with col3:
        seasons = run_query("SELECT COUNT(DISTINCT season) as cnt FROM matches")
        st.metric("Seasons", seasons['cnt'].iloc[0])

    with col4:
        players = run_query("SELECT COUNT(*) as cnt FROM people")
        st.metric("Players in Registry", f"{players['cnt'].iloc[0]:,}")

    st.divider()

    # Matches per season
    st.subheader("Matches per Season")
    season_data = run_query("""
        SELECT season, COUNT(*) as matches
        FROM matches
        WHERE season IS NOT NULL
        GROUP BY season
        ORDER BY season
    """)
    st.bar_chart(season_data.set_index('season'))

    # Top teams by wins
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Most Successful Teams")
        team_wins = run_query("""
            SELECT winner as team, COUNT(*) as wins
            FROM matches
            WHERE winner IS NOT NULL
            GROUP BY winner
            ORDER BY wins DESC
            LIMIT 10
        """)
        st.dataframe(team_wins, use_container_width=True, hide_index=True)

    with col2:
        st.subheader("Top Player of Match Awards")
        pom = run_query("""
            SELECT m.player_of_match as player,
                   'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.key_cricinfo || '.png' as photo_url,
                   COUNT(*) as awards
            FROM matches m
            LEFT JOIN people p ON m.player_of_match = p.name
            WHERE m.player_of_match IS NOT NULL
            GROUP BY m.player_of_match, p.key_cricinfo
            ORDER BY awards DESC
            LIMIT 10
        """)
        st.dataframe(pom[['player', 'awards']], use_container_width=True, hide_index=True)

    # Top 5 award winners with photos
    st.subheader("Most Decorated Players")
    top_pom = run_query("""
        SELECT m.player_of_match as player,
               'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.key_cricinfo || '.png' as photo_url,
               COUNT(*) as awards
        FROM matches m
        LEFT JOIN people p ON m.player_of_match = p.name
        WHERE m.player_of_match IS NOT NULL
        GROUP BY m.player_of_match, p.key_cricinfo
        ORDER BY awards DESC
        LIMIT 5
    """)
    display_player_cards(top_pom, 'player', 'awards', 'Awards', limit=5)

# IPL Winners page
elif page == "IPL Winners":
    st.title("🏆 IPL Champions by Year")

    # Get final match of each season (highest match_number or latest date)
    winners = run_query("""
        WITH finals AS (
            SELECT
                season,
                match_id,
                match_date,
                team1,
                team2,
                winner,
                CASE
                    WHEN win_by_runs > 0 THEN win_by_runs || ' runs'
                    WHEN win_by_wickets > 0 THEN win_by_wickets || ' wickets'
                    ELSE 'N/A'
                END as margin,
                player_of_match,
                city,
                ROW_NUMBER() OVER (PARTITION BY season ORDER BY match_date DESC, match_number DESC) as rn
            FROM matches
            WHERE winner IS NOT NULL
        )
        SELECT
            season as "Season",
            winner as "Champion",
            CASE
                WHEN team1 = winner THEN team2
                ELSE team1
            END as "Runner-up",
            margin as "Victory Margin",
            player_of_match as "Finals MVP",
            city as "Venue"
        FROM finals
        WHERE rn = 1
        ORDER BY season DESC
    """)

    # Display trophy count
    st.subheader("Trophy Cabinet")
    trophy_count = run_query("""
        WITH finals AS (
            SELECT season, winner,
                   ROW_NUMBER() OVER (PARTITION BY season ORDER BY match_date DESC, match_number DESC) as rn
            FROM matches
            WHERE winner IS NOT NULL
        )
        SELECT winner as team, COUNT(*) as titles
        FROM finals
        WHERE rn = 1
        GROUP BY winner
        ORDER BY titles DESC
    """)

    # Display as columns with trophy emoji
    cols = st.columns(len(trophy_count))
    for i, (idx, row) in enumerate(trophy_count.iterrows()):
        with cols[i]:
            trophies = "🏆" * row['titles']
            st.markdown(f"**{row['team']}**")
            st.markdown(f"{trophies}")
            st.caption(f"{row['titles']} title(s)")

    st.divider()

    # Full winners table
    st.subheader("Season-wise Champions")
    st.dataframe(winners, use_container_width=True, hide_index=True)

    # Visualize wins by team
    st.subheader("Titles Won by Team")
    st.bar_chart(trophy_count.set_index('team')['titles'])

# Batting Stats page
elif page == "Batting Stats":
    st.title("🏏 Batting Statistics")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        seasons = run_query("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season")
        selected_seasons = st.multiselect("Select Seasons", seasons['season'].tolist(), default=seasons['season'].tolist())

    with col2:
        min_runs = st.slider("Minimum Runs", 0, 1000, 100)

    if selected_seasons:
        season_filter = ",".join([f"'{s}'" for s in selected_seasons])

        # Top run scorers with photos
        st.subheader("Top Run Scorers")
        batting = run_query(f"""
            SELECT
                d.batter,
                p.key_cricinfo,
                'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.key_cricinfo || '.png' as photo_url,
                COUNT(DISTINCT d.match_id) as matches,
                SUM(d.batter_runs) as runs,
                COUNT(CASE WHEN d.batter_runs > 0 THEN 1 END) as balls_faced,
                SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
                ROUND(SUM(d.batter_runs) * 100.0 / NULLIF(COUNT(CASE WHEN d.batter_runs >= 0 AND d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%' THEN 1 END), 0), 2) as strike_rate
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            LEFT JOIN people p ON d.batter = p.name
            WHERE m.season IN ({season_filter})
            GROUP BY d.batter, p.key_cricinfo
            HAVING SUM(d.batter_runs) >= {min_runs}
            ORDER BY runs DESC
            LIMIT 20
        """)

        # Display top 5 with photos
        if len(batting) > 0:
            display_player_cards(batting, 'batter', 'runs', 'Runs', limit=5)
            st.divider()

        # Full table (hide photo columns)
        display_cols = [c for c in batting.columns if c not in ['key_cricinfo', 'photo_url']]
        st.dataframe(batting[display_cols], use_container_width=True, hide_index=True)

        # Top individual scores
        st.subheader("Highest Individual Scores")
        high_scores = run_query(f"""
            SELECT
                d.batter,
                d.match_id,
                m.match_date,
                d.batting_team,
                SUM(d.batter_runs) as runs,
                SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as fours,
                SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as sixes
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE m.season IN ({season_filter})
            GROUP BY d.batter, d.match_id, m.match_date, d.batting_team
            ORDER BY runs DESC
            LIMIT 15
        """)
        st.dataframe(high_scores, use_container_width=True, hide_index=True)

# Bowling Stats page
elif page == "Bowling Stats":
    st.title("🎳 Bowling Statistics")

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        seasons = run_query("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season")
        selected_seasons = st.multiselect("Select Seasons", seasons['season'].tolist(), default=seasons['season'].tolist(), key="bowl_seasons")

    with col2:
        min_wickets = st.slider("Minimum Wickets", 0, 50, 10)

    if selected_seasons:
        season_filter = ",".join([f"'{s}'" for s in selected_seasons])

        # Top wicket takers with photos
        st.subheader("Top Wicket Takers")
        bowling = run_query(f"""
            SELECT
                d.bowler,
                p.key_cricinfo,
                'https://a.espncdn.com/i/headshots/cricket/players/full/' || p.key_cricinfo || '.png' as photo_url,
                COUNT(DISTINCT d.match_id) as matches,
                SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END) as wickets,
                SUM(d.total_runs) as runs_conceded,
                COUNT(*) as balls,
                ROUND(SUM(d.total_runs) * 6.0 / NULLIF(COUNT(*), 0), 2) as economy,
                ROUND(COUNT(*) * 1.0 / NULLIF(SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END), 0), 2) as strike_rate
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            LEFT JOIN people p ON d.bowler = p.name
            WHERE m.season IN ({season_filter})
            GROUP BY d.bowler, p.key_cricinfo
            HAVING SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END) >= {min_wickets}
            ORDER BY wickets DESC
            LIMIT 20
        """)

        # Display top 5 with photos
        if len(bowling) > 0:
            display_player_cards(bowling, 'bowler', 'wickets', 'Wickets', limit=5)
            st.divider()

        # Full table (hide photo columns)
        display_cols = [c for c in bowling.columns if c not in ['key_cricinfo', 'photo_url']]
        st.dataframe(bowling[display_cols], use_container_width=True, hide_index=True)

        # Best bowling figures
        st.subheader("Best Bowling Figures (Single Match)")
        best_figures = run_query(f"""
            SELECT
                d.bowler,
                d.match_id,
                m.match_date,
                SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END) as wickets,
                SUM(d.total_runs) as runs
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE m.season IN ({season_filter})
            GROUP BY d.bowler, d.match_id, m.match_date
            HAVING SUM(CASE WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'obstructing the field') THEN 1 ELSE 0 END) >= 3
            ORDER BY wickets DESC, runs ASC
            LIMIT 15
        """)
        st.dataframe(best_figures, use_container_width=True, hide_index=True)

# Match Analysis page
elif page == "Match Analysis":
    st.title("📊 Match Analysis")

    # Season and match selection
    seasons = run_query("SELECT DISTINCT season FROM matches WHERE season IS NOT NULL ORDER BY season DESC")
    selected_season = st.selectbox("Select Season", seasons['season'].tolist())

    matches = run_query(f"""
        SELECT match_id, match_date, team1 || ' vs ' || team2 as match_name, city
        FROM matches
        WHERE season = '{selected_season}'
        ORDER BY match_date DESC
    """)

    match_options = dict(zip(matches['match_id'], matches['match_name'] + ' (' + matches['match_date'].astype(str) + ')'))
    selected_match = st.selectbox("Select Match", list(match_options.keys()), format_func=lambda x: match_options[x])

    if selected_match:
        # Match details
        match_info = run_query(f"""
            SELECT * FROM matches WHERE match_id = '{selected_match}'
        """)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Venue", match_info['city'].iloc[0] or "N/A")
        with col2:
            st.metric("Winner", match_info['winner'].iloc[0] or "No Result")
        with col3:
            st.metric("Player of Match", match_info['player_of_match'].iloc[0] or "N/A")

        st.divider()

        # Innings breakdown
        for innings in [1, 2]:
            innings_data = run_query(f"""
                SELECT batting_team FROM deliveries
                WHERE match_id = '{selected_match}' AND innings = {innings}
                LIMIT 1
            """)

            if len(innings_data) > 0:
                team = innings_data['batting_team'].iloc[0]
                st.subheader(f"Innings {innings}: {team}")

                # Batting scorecard
                scorecard = run_query(f"""
                    SELECT
                        batter,
                        SUM(batter_runs) as runs,
                        COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) as balls,
                        SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as fours,
                        SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as sixes,
                        MAX(CASE WHEN is_wicket AND wicket_player_out = batter THEN wicket_kind ELSE NULL END) as dismissal
                    FROM deliveries
                    WHERE match_id = '{selected_match}' AND innings = {innings}
                    GROUP BY batter
                    ORDER BY MIN(over_number), MIN(ball_number)
                """)
                st.dataframe(scorecard, use_container_width=True, hide_index=True)

# Head to Head page
elif page == "Head to Head":
    st.title("⚔️ Head to Head")

    teams = run_query("""
        SELECT DISTINCT team FROM (
            SELECT team1 as team FROM matches
            UNION
            SELECT team2 as team FROM matches
        ) WHERE team IS NOT NULL
        ORDER BY team
    """)

    col1, col2 = st.columns(2)
    with col1:
        team1 = st.selectbox("Team 1", teams['team'].tolist())
    with col2:
        team2 = st.selectbox("Team 2", teams['team'].tolist(), index=1)

    if team1 and team2 and team1 != team2:
        h2h = run_query(f"""
            SELECT
                COUNT(*) as total_matches,
                SUM(CASE WHEN winner = '{team1}' THEN 1 ELSE 0 END) as team1_wins,
                SUM(CASE WHEN winner = '{team2}' THEN 1 ELSE 0 END) as team2_wins,
                SUM(CASE WHEN winner IS NULL OR (winner != '{team1}' AND winner != '{team2}') THEN 1 ELSE 0 END) as no_result
            FROM matches
            WHERE (team1 = '{team1}' AND team2 = '{team2}')
               OR (team1 = '{team2}' AND team2 = '{team1}')
        """)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Matches", h2h['total_matches'].iloc[0])
        with col2:
            st.metric(f"{team1} Wins", h2h['team1_wins'].iloc[0])
        with col3:
            st.metric(f"{team2} Wins", h2h['team2_wins'].iloc[0])
        with col4:
            st.metric("No Result", h2h['no_result'].iloc[0])

        st.divider()

        # Recent matches
        st.subheader("Recent Matches")
        recent = run_query(f"""
            SELECT match_date, city, winner,
                   CASE WHEN win_by_runs > 0 THEN win_by_runs || ' runs'
                        WHEN win_by_wickets > 0 THEN win_by_wickets || ' wickets'
                        ELSE 'N/A' END as margin,
                   player_of_match
            FROM matches
            WHERE (team1 = '{team1}' AND team2 = '{team2}')
               OR (team1 = '{team2}' AND team2 = '{team1}')
            ORDER BY match_date DESC
            LIMIT 10
        """)
        st.dataframe(recent, use_container_width=True, hide_index=True)

# SQL Query page
elif page == "SQL Query":
    st.title("🔍 SQL Query Editor")

    st.markdown("""
    **Available Tables:**
    - `matches` - Match details (1,169 rows)
    - `deliveries` - Ball-by-ball data (278,205 rows)
    - `people` - Player registry (17,562 rows)
    """)

    # Sample queries
    with st.expander("Sample Queries"):
        st.code("""
-- Top 10 run scorers
SELECT batter, SUM(batter_runs) as runs
FROM deliveries
GROUP BY batter
ORDER BY runs DESC
LIMIT 10;

-- Matches per venue
SELECT city, COUNT(*) as matches
FROM matches
GROUP BY city
ORDER BY matches DESC;

-- Best strike rates (min 500 runs)
SELECT batter,
       SUM(batter_runs) as runs,
       COUNT(*) as balls,
       ROUND(SUM(batter_runs) * 100.0 / COUNT(*), 2) as strike_rate
FROM deliveries
GROUP BY batter
HAVING SUM(batter_runs) >= 500
ORDER BY strike_rate DESC
LIMIT 10;
        """, language="sql")

    # Query input
    query = st.text_area("Enter SQL Query", height=150, value="SELECT * FROM matches LIMIT 10")

    if st.button("Run Query", type="primary"):
        try:
            result = run_query(query)
            st.success(f"Query returned {len(result)} rows")
            st.dataframe(result, use_container_width=True, hide_index=True)

            # Download button
            csv = result.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="query_result.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error: {e}")

# Footer
st.sidebar.divider()
st.sidebar.markdown("Data source: [Cricsheet](https://cricsheet.org)")
