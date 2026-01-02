#!/usr/bin/env python3
"""Streamlit app for exploring IPL cricket data using dbt semantic layer."""

import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import os
import requests

# Page config
st.set_page_config(
    page_title="IPL Data Explorer",
    page_icon="🏏",
    layout="wide"
)

# Custom CSS for consistent image sizing
st.markdown("""
<style>
/* Fix for st.image to have consistent sizing */
[data-testid="stImage"] {
    display: flex;
    justify-content: center;
}
[data-testid="stImage"] img {
    width: 100px !important;
    height: 100px !important;
    object-fit: cover;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

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

# Logo directory path
LOGO_DIR = Path(__file__).parent / "logos"
PLAYER_PLACEHOLDER = LOGO_DIR / "player_placeholder.png"

def get_team_logo_path(team_name):
    """Get local path for team logo."""
    if not team_name:
        return None
    filename = team_name.lower().replace(' ', '_') + '.png'
    logo_path = LOGO_DIR / filename
    if logo_path.exists():
        return str(logo_path)
    return None

def display_team_logo(team_name, size=80):
    """Display team logo with proper sizing using HTML/CSS to prevent distortion."""
    logo_path = get_team_logo_path(team_name)
    if logo_path:
        import base64
        with open(logo_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{data}" style="max-width:{size}px; max-height:{size}px; object-fit:contain;">',
            unsafe_allow_html=True
        )

@st.cache_data(ttl=3600)
def check_image_exists(url):
    """Check if image URL returns valid response."""
    try:
        resp = requests.head(url, timeout=2)
        return resp.status_code == 200
    except (requests.RequestException, requests.Timeout):
        return False

def display_player_cards(df, name_col, stat_col, stat_label, limit=5):
    """Display player cards with photos."""
    cols = st.columns(limit)
    for i, (idx, row) in enumerate(df.head(limit).iterrows()):
        with cols[i]:
            photo_url = row.get('photo_url')
            show_placeholder = True
            if photo_url and pd.notna(row.get('key_cricinfo')):
                if check_image_exists(photo_url):
                    st.image(photo_url, width=100)
                    show_placeholder = False
            if show_placeholder and PLAYER_PLACEHOLDER.exists():
                st.image(str(PLAYER_PLACEHOLDER), width=100)
            st.markdown(f"**{row[name_col]}**")
            val = row[stat_col]
            if isinstance(val, (int, float)):
                st.metric(stat_label, f"{int(val):,}")
            else:
                st.metric(stat_label, val)

# Sidebar navigation
st.sidebar.title("🏏 IPL Explorer")

# Check for query parameters (for direct links to match analysis)
nav_pages = ["Overview", "Player Stats", "Match Analysis", "Head to Head", "Impact Players", "SQL Query", "Feedback"]

# Initialize the page in session state if not present
if 'current_nav_page' not in st.session_state:
    st.session_state['current_nav_page'] = "Overview"

# Handle query params for direct navigation
try:
    if hasattr(st, 'query_params'):
        qp_page = st.query_params.get('page', '')
        qp_match_id = st.query_params.get('match_id', '')
        qp_season = st.query_params.get('season', '')
    else:
        params = st.experimental_get_query_params()
        qp_page = params.get('page', [''])[0]
        qp_match_id = params.get('match_id', [''])[0]
        qp_season = params.get('season', [''])[0]
except:
    qp_page = qp_match_id = qp_season = ''

# URL decode the page name (Match+Analysis -> Match Analysis)
if qp_page:
    qp_page = qp_page.replace('+', ' ')

# Check if we need to navigate to Match Analysis via query params
if qp_page == 'Match Analysis' and qp_match_id:
    # Only process if we haven't already stored these params
    if st.session_state.get('last_qp_match_id') != qp_match_id:
        st.session_state['qp_match_id'] = qp_match_id
        st.session_state['qp_season'] = qp_season
        st.session_state['current_nav_page'] = "Match Analysis"
        st.session_state['last_qp_match_id'] = qp_match_id  # Prevent re-processing
        st.rerun()

# Check if we need to navigate via session state
if st.session_state.get('navigate_to_match'):
    st.session_state['current_nav_page'] = "Match Analysis"
    st.session_state['navigate_to_match'] = False
    st.rerun()

# Use session state as the source of truth for the page
page = st.session_state['current_nav_page']

# Sidebar navigation radio (display only, session state is source of truth)
selected_page = st.sidebar.radio(
    "Navigate",
    nav_pages,
    index=nav_pages.index(page),
    key="nav_radio_widget"
)

# If user clicked a different page in the sidebar, update and rerun
if selected_page != page:
    st.session_state['current_nav_page'] = selected_page
    st.rerun()

# Overview page - IPL Champions
if page == "Overview":
    st.title("🏏 IPL Data Explorer")

    # Get final match of each season from staging model
    winners = run_query("""
        WITH finals AS (
            SELECT
                season,
                match_id,
                match_date,
                REPLACE(REPLACE(team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team1,
                REPLACE(REPLACE(team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team2,
                REPLACE(REPLACE(winner, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as winner,
                CASE
                    WHEN win_by_runs > 0 THEN win_by_runs || ' runs'
                    WHEN win_by_wickets > 0 THEN win_by_wickets || ' wickets'
                    ELSE 'N/A'
                END as margin,
                player_of_match,
                COALESCE(venue, city) as venue_or_city,
                ROW_NUMBER() OVER (PARTITION BY season ORDER BY match_date DESC, match_number DESC) as rn
            FROM stg_matches
            WHERE winner IS NOT NULL
        )
        SELECT
            season as "Season",
            match_id,
            winner as "Champion",
            CASE
                WHEN team1 = winner THEN team2
                ELSE team1
            END as "Runner-up",
            margin as "Victory Margin",
            player_of_match as "Finals MVP",
            venue_or_city as "Venue"
        FROM finals
        WHERE rn = 1
        ORDER BY season DESC
    """)

    # Display trophy count with years
    st.subheader("Trophy Cabinet")
    trophy_count = run_query("""
        WITH finals AS (
            SELECT season,
                   REPLACE(REPLACE(winner, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as winner,
                   ROW_NUMBER() OVER (PARTITION BY season ORDER BY match_date DESC, match_number DESC) as rn
            FROM stg_matches
            WHERE winner IS NOT NULL
        ),
        team_titles AS (
            SELECT winner as team, season
            FROM finals
            WHERE rn = 1
        )
        SELECT
            team,
            COUNT(*) as titles,
            STRING_AGG(season, ', ' ORDER BY season) as years,
            MAX(season) as latest_win
        FROM team_titles
        GROUP BY team
        ORDER BY titles DESC, latest_win ASC
    """)

    # Display as columns with team logos and trophy emoji - evenly distributed
    num_teams = len(trophy_count)
    cols = st.columns(num_teams)
    for i, (idx, row) in enumerate(trophy_count.iterrows()):
        with cols[i]:
            display_team_logo(row['team'], size=80)
            trophies = "🏆" * row['titles']
            st.markdown(f"**{row['team']}**")
            st.markdown(f"{trophies}")
            st.caption(f"{row['years']}")

    st.divider()

    # Full winners table with link to match analysis
    st.subheader("Season-wise Champions")

    # Build display dataframe with clickable scorecard links
    display_df = winners[['Season', 'Champion', 'Runner-up', 'Victory Margin', 'Finals MVP', 'Venue', 'match_id']].copy()

    # Create clickable links using markdown
    display_df['Scorecard'] = display_df.apply(
        lambda row: f"[📊 View](?page=Match+Analysis&match_id={row['match_id']}&season={row['Season']})",
        axis=1
    )

    # Display table with markdown links
    st.markdown(
        display_df[['Season', 'Champion', 'Runner-up', 'Victory Margin', 'Finals MVP', 'Venue', 'Scorecard']].to_markdown(index=False),
        unsafe_allow_html=True
    )

    st.divider()

    # Team Performance by Season - Matrix view
    st.subheader("Team Performance by Season")
    st.caption("Win percentage by team across seasons")

    # IPL Team Colors
    TEAM_COLORS = {
        'Chennai Super Kings': '#FFCB05',
        'Mumbai Indians': '#004BA0',
        'Royal Challengers Bengaluru': '#EC1C24',
        'Royal Challengers Bangalore': '#EC1C24',
        'Kolkata Knight Riders': '#3A225D',
        'Delhi Capitals': '#004C93',
        'Delhi Daredevils': '#004C93',
        'Punjab Kings': '#DD1F2D',
        'Kings XI Punjab': '#DD1F2D',
        'Rajasthan Royals': '#EA1A85',
        'Sunrisers Hyderabad': '#F7A721',
        'Gujarat Titans': '#0B4973',
        'Lucknow Super Giants': '#00A9E0',
        'Deccan Chargers': '#D5A239',
        'Pune Warriors': '#2F9BE3',
        'Gujarat Lions': '#E04F16',
        'Rising Pune Supergiant': '#6F61A0',
        'Rising Pune Supergiants': '#6F61A0',
        'Kochi Tuskers Kerala': '#FF6B00',
    }

    team_season_perf = run_query("""
        WITH team_season AS (
            SELECT
                season,
                REPLACE(REPLACE(team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team,
                CASE WHEN REPLACE(REPLACE(winner, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') = REPLACE(REPLACE(team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 1 ELSE 0 END as won
            FROM stg_matches
            WHERE winner IS NOT NULL
            UNION ALL
            SELECT
                season,
                REPLACE(REPLACE(team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team,
                CASE WHEN REPLACE(REPLACE(winner, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') = REPLACE(REPLACE(team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') THEN 1 ELSE 0 END as won
            FROM stg_matches
            WHERE winner IS NOT NULL
        ),
        team_totals AS (
            SELECT team, COUNT(*) as total_matches
            FROM team_season
            GROUP BY team
        )
        SELECT
            ts.team,
            ts.season,
            COUNT(*) as matches,
            SUM(ts.won) as wins,
            ROUND(SUM(ts.won) * 100.0 / COUNT(*), 0) as win_pct,
            tt.total_matches
        FROM team_season ts
        JOIN team_totals tt ON ts.team = tt.team
        GROUP BY ts.team, ts.season, tt.total_matches
        ORDER BY tt.total_matches DESC, ts.team, ts.season
    """)

    if len(team_season_perf) > 0:
        # Get championship winners for gold outline
        champions = set()
        for idx, row in winners.iterrows():
            champions.add((row['Champion'], row['Season']))

        # Get team order by total matches
        team_order = team_season_perf.groupby('team')['total_matches'].first().sort_values(ascending=False).index.tolist()

        # Create pivot table for matrix view
        matrix = team_season_perf.pivot(index='team', columns='season', values='win_pct').fillna(-1)
        # Reorder rows by total matches played
        matrix = matrix.reindex(team_order)

        # Style function to color cells based on win percentage and championship
        def style_matrix_with_champions(row):
            team = row.name
            styles = []
            for season in row.index:
                val = matrix.loc[team, season]  # Get original numeric value
                # Base style based on win percentage
                if val == -1:
                    style = 'background-color: #f0f0f0; color: #999'
                elif val >= 60:
                    style = 'background-color: #28a745; color: white'
                elif val >= 50:
                    style = 'background-color: #90EE90; color: black'
                elif val >= 40:
                    style = 'background-color: #FFD700; color: black'
                else:
                    style = 'background-color: #FF6B6B; color: white'

                # Add gold outline if team won championship that season
                if (team, season) in champions:
                    style += '; outline: 3px solid #FFD700; outline-offset: -3px'

                styles.append(style)
            return styles

        # Custom formatter that includes trophy
        def format_cell(v, team, season):
            if v == -1:
                return '-'
            if (team, season) in champions:
                return f"🏆{int(v)}%"
            return f"{int(v)}%"

        # Create formatted matrix with trophy emoji
        formatted = matrix.copy().astype(object)
        for team in formatted.index:
            for season in formatted.columns:
                formatted.loc[team, season] = format_cell(matrix.loc[team, season], team, season)

        # Calculate height to show all rows (approx 35px per row + header)
        table_height = (len(matrix) + 1) * 35 + 10

        # Apply styling and display
        styled_formatted = formatted.style.apply(style_matrix_with_champions, axis=1)
        st.dataframe(styled_formatted, use_container_width=True, height=table_height)

        st.caption("🟢 60%+ | 🟡 50-59% | 🟠 40-49% | 🔴 <40% | 🏆 = Championship winner")

# Player Stats page - combines Batting and Bowling
elif page == "Player Stats":
    st.title("📊 Player Statistics")

    tab1, tab2 = st.tabs(["Batting", "Bowling"])

    with tab1:
        st.caption("Data from dbt semantic layer: batting_metrics")

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            min_runs = st.slider("Minimum Runs", 0, 1000, 100)

        with col2:
            min_matches = st.slider("Minimum Matches", 1, 50, 10)

        # Top run scorers from batting_metrics semantic model
        st.subheader("Top Run Scorers")
        batting = run_query(f"""
            SELECT
                batter,
                cricinfo_id as key_cricinfo,
                'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
                matches,
                innings,
                total_runs as runs,
                total_balls as balls,
                batting_average as average,
                strike_rate,
                total_fours as fours,
                total_sixes as sixes,
                fifties,
                centuries,
                highest_score
            FROM batting_metrics
            WHERE total_runs >= {min_runs} AND matches >= {min_matches}
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

        # Best strike rates
        st.subheader("Best Strike Rates (min 500 runs)")
        strike_rates = run_query("""
            SELECT batter, total_runs as runs, total_balls as balls, strike_rate
            FROM batting_metrics
            WHERE total_runs >= 500
            ORDER BY strike_rate DESC
            LIMIT 15
        """)
        st.dataframe(strike_rates, use_container_width=True, hide_index=True)

        # Best averages
        st.subheader("Best Batting Averages (min 500 runs)")
        averages = run_query("""
            SELECT batter, total_runs as runs, dismissals, batting_average as average
            FROM batting_metrics
            WHERE total_runs >= 500
            ORDER BY average DESC
            LIMIT 15
        """)
        st.dataframe(averages, use_container_width=True, hide_index=True)

    with tab2:
        st.caption("Data from dbt semantic layer: bowling_metrics")

        # Filters
        col1, col2 = st.columns(2)

        with col1:
            min_wickets = st.slider("Minimum Wickets", 0, 50, 10)

        with col2:
            min_matches_bowl = st.slider("Minimum Matches", 1, 50, 10, key="bowl_matches")

        # Top wicket takers from bowling_metrics semantic model
        st.subheader("Top Wicket Takers")
        bowling = run_query(f"""
            SELECT
                bowler,
                cricinfo_id as key_cricinfo,
                'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
                matches,
                innings,
                overs,
                total_wickets as wickets,
                total_runs_conceded as runs,
                bowling_average as average,
                economy_rate as economy,
                strike_rate,
                best_bowling,
                four_wicket_hauls as "4W",
                five_wicket_hauls as "5W"
            FROM bowling_metrics
            WHERE total_wickets >= {min_wickets} AND matches >= {min_matches_bowl}
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

        # Best economy rates
        st.subheader("Best Economy Rates (min 50 wickets)")
        economy = run_query("""
            SELECT bowler, total_wickets as wickets, overs, economy_rate as economy
            FROM bowling_metrics
            WHERE total_wickets >= 50
            ORDER BY economy ASC
            LIMIT 15
        """)
        st.dataframe(economy, use_container_width=True, hide_index=True)

        # Best bowling averages
        st.subheader("Best Bowling Averages (min 50 wickets)")
        bowl_avg = run_query("""
            SELECT bowler, total_wickets as wickets, total_runs_conceded as runs, bowling_average as average
            FROM bowling_metrics
            WHERE total_wickets >= 50
            ORDER BY average ASC
            LIMIT 15
        """)
        st.dataframe(bowl_avg, use_container_width=True, hide_index=True)

# Match Analysis page - uses stg_matches and stg_deliveries from semantic layer
elif page == "Match Analysis":
    # Check if navigated from IPL Champions (via session state) or query params
    pre_selected_season = st.session_state.pop('selected_season', None) or st.session_state.pop('qp_season', None)
    pre_selected_match = st.session_state.pop('selected_match_id', None) or st.session_state.pop('qp_match_id', None)

    # Convert match_id to int if it's a string (from query params)
    if pre_selected_match and isinstance(pre_selected_match, str):
        try:
            pre_selected_match = int(pre_selected_match)
        except ValueError:
            pre_selected_match = None

    # Scroll to top if navigated from another page
    if pre_selected_season or pre_selected_match:
        import streamlit.components.v1 as components
        components.html(
            """
            <script>
                window.parent.document.querySelector('section.main').scrollTo(0, 0);
            </script>
            """,
            height=0
        )

    st.title("📊 Match Scorecard")

    # Season and match selection from staging model
    seasons = run_query("SELECT DISTINCT season FROM stg_matches WHERE season IS NOT NULL ORDER BY season DESC")
    season_list = seasons['season'].tolist()

    # Pre-select season if coming from IPL Champions or query params
    default_season_idx = 0
    if pre_selected_season and pre_selected_season in season_list:
        default_season_idx = season_list.index(pre_selected_season)

    selected_season = st.selectbox("Select Season", season_list, index=default_season_idx)

    matches = run_query(f"""
        SELECT match_id, match_date,
               REPLACE(REPLACE(team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') || ' vs ' ||
               REPLACE(REPLACE(team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as match_name,
               city
        FROM stg_matches
        WHERE season = '{selected_season}'
        ORDER BY match_date DESC
    """)

    match_options = dict(zip(matches['match_id'], matches['match_name'] + ' (' + matches['match_date'].astype(str) + ')'))
    match_list = list(match_options.keys())

    # Pre-select match if coming from IPL Champions or query params
    default_match_idx = 0
    if pre_selected_match and pre_selected_match in match_list:
        default_match_idx = match_list.index(pre_selected_match)

    selected_match = st.selectbox("Select Match", match_list, index=default_match_idx, format_func=lambda x: match_options[x])

    if selected_match:
        # Match details from staging model
        match_info = run_query(f"""
            SELECT * FROM stg_matches WHERE match_id = '{selected_match}'
        """)

        # Get innings totals for header
        innings_totals = run_query(f"""
            SELECT
                innings,
                REPLACE(REPLACE(batting_team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as batting_team,
                SUM(total_runs) as total,
                SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) as wickets,
                MAX(over_number) as overs,
                MAX(ball_number) as last_ball
            FROM stg_deliveries
            WHERE match_id = '{selected_match}'
            GROUP BY innings, REPLACE(REPLACE(batting_team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant')
            ORDER BY innings
        """)

        # Match Header with team scores
        st.markdown("---")
        header_cols = st.columns([2, 1, 2])

        team1_data = innings_totals[innings_totals['innings'] == 1].iloc[0] if len(innings_totals) > 0 else None
        team2_data = innings_totals[innings_totals['innings'] == 2].iloc[0] if len(innings_totals) > 1 else None

        with header_cols[0]:
            if team1_data is not None:
                display_team_logo(team1_data['batting_team'], size=60)
                st.markdown(f"### {team1_data['batting_team']}")
                overs_str = f"{int(team1_data['overs'])}.{int(team1_data['last_ball'])}"
                st.markdown(f"## {int(team1_data['total'])}/{int(team1_data['wickets'])}")
                st.caption(f"({overs_str} overs)")

        with header_cols[1]:
            st.markdown("<div style='text-align: center; padding-top: 30px;'><h3>vs</h3></div>", unsafe_allow_html=True)

        with header_cols[2]:
            if team2_data is not None:
                display_team_logo(team2_data['batting_team'], size=60)
                st.markdown(f"### {team2_data['batting_team']}")
                overs_str = f"{int(team2_data['overs'])}.{int(team2_data['last_ball'])}"
                st.markdown(f"## {int(team2_data['total'])}/{int(team2_data['wickets'])}")
                st.caption(f"({overs_str} overs)")

        # Result (normalize team name)
        winner_raw = match_info['winner'].iloc[0]
        winner = winner_raw.replace('Royal Challengers Bangalore', 'Royal Challengers Bengaluru').replace('Rising Pune Supergiants', 'Rising Pune Supergiant') if winner_raw else None
        if winner:
            win_runs = match_info['win_by_runs'].iloc[0]
            win_wickets = match_info['win_by_wickets'].iloc[0]
            if pd.notna(win_runs) and win_runs > 0:
                result = f"{winner} won by {int(win_runs)} runs"
            elif pd.notna(win_wickets) and win_wickets > 0:
                result = f"{winner} won by {int(win_wickets)} wickets"
            else:
                result = f"{winner} won"
            st.success(f"**{result}**")
        else:
            st.info("No Result")

        # Match info bar (normalize toss_winner)
        toss_winner = match_info['toss_winner'].iloc[0]
        toss_winner = toss_winner.replace('Royal Challengers Bangalore', 'Royal Challengers Bengaluru').replace('Rising Pune Supergiants', 'Rising Pune Supergiant') if toss_winner else 'N/A'
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.caption(f"**Venue:** {match_info['venue'].iloc[0] or match_info['city'].iloc[0] or 'N/A'}")
        with col2:
            st.caption(f"**Date:** {match_info['match_date'].iloc[0]}")
        with col3:
            st.caption(f"**Toss:** {toss_winner} ({match_info['toss_decision'].iloc[0]})")
        with col4:
            st.caption(f"**Player of Match:** {match_info['player_of_match'].iloc[0] or 'N/A'}")

        st.markdown("---")

        # Innings scorecards
        for innings in [1, 2]:
            innings_data = run_query(f"""
                SELECT REPLACE(REPLACE(batting_team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as batting_team
                FROM stg_deliveries
                WHERE match_id = '{selected_match}' AND innings = {innings}
                LIMIT 1
            """)

            if len(innings_data) > 0:
                team = innings_data['batting_team'].iloc[0]
                inn_total = innings_totals[innings_totals['innings'] == innings].iloc[0]

                with st.expander(f"**{team} Innings - {int(inn_total['total'])}/{int(inn_total['wickets'])}**", expanded=True):

                    # BATTING SCORECARD
                    st.markdown("##### Batting")

                    batting = run_query(f"""
                        SELECT
                            batter,
                            SUM(batter_runs) as R,
                            COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) as B,
                            SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as "4s",
                            SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as "6s",
                            ROUND(SUM(batter_runs) * 100.0 / NULLIF(COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END), 0), 2) as SR,
                            MAX(CASE WHEN is_wicket AND wicket_player_out = batter THEN wicket_kind ELSE NULL END) as dismissal_type,
                            MAX(CASE WHEN is_wicket AND wicket_player_out = batter THEN bowler ELSE NULL END) as dismissal_bowler,
                            MAX(CASE WHEN is_wicket AND wicket_player_out = batter THEN wicket_fielders ELSE NULL END) as fielder
                        FROM stg_deliveries
                        WHERE match_id = '{selected_match}' AND innings = {innings}
                        GROUP BY batter
                        ORDER BY MIN(over_number), MIN(ball_number)
                    """)

                    # Format dismissal column
                    def format_dismissal(row):
                        if pd.isna(row['dismissal_type']) or row['dismissal_type'] is None:
                            return "not out"
                        d_type = row['dismissal_type']
                        bowler = row['dismissal_bowler'] or ""
                        fielder = row['fielder'] or ""
                        if d_type == 'bowled':
                            return f"b {bowler}"
                        elif d_type == 'caught':
                            if fielder and bowler:
                                return f"c {fielder.split(',')[0]} b {bowler}"
                            return f"c & b {bowler}"
                        elif d_type == 'lbw':
                            return f"lbw b {bowler}"
                        elif d_type == 'stumped':
                            return f"st {fielder.split(',')[0] if fielder else '†'} b {bowler}"
                        elif d_type == 'run out':
                            return f"run out ({fielder.split(',')[0] if fielder else ''})"
                        elif d_type == 'caught and bowled':
                            return f"c & b {bowler}"
                        elif d_type == 'hit wicket':
                            return f"hit wicket b {bowler}"
                        else:
                            return d_type

                    batting['Dismissal'] = batting.apply(format_dismissal, axis=1)
                    batting_display = batting[['batter', 'Dismissal', 'R', 'B', '4s', '6s', 'SR']].copy()
                    batting_display.columns = ['Batter', 'Dismissal', 'R', 'B', '4s', '6s', 'SR']

                    # Style not out batters
                    st.dataframe(batting_display, use_container_width=True, hide_index=True)

                    # Extras
                    extras = run_query(f"""
                        SELECT
                            SUM(CASE WHEN extras_type LIKE '%wides%' THEN extras_runs ELSE 0 END) as wides,
                            SUM(CASE WHEN extras_type LIKE '%noballs%' THEN extras_runs ELSE 0 END) as noballs,
                            SUM(CASE WHEN extras_type LIKE '%byes%' THEN extras_runs ELSE 0 END) as byes,
                            SUM(CASE WHEN extras_type LIKE '%legbyes%' THEN extras_runs ELSE 0 END) as legbyes,
                            SUM(extras_runs) as total_extras
                        FROM stg_deliveries
                        WHERE match_id = '{selected_match}' AND innings = {innings}
                    """)

                    if len(extras) > 0:
                        e = extras.iloc[0]
                        extras_parts = []
                        if e['wides'] > 0: extras_parts.append(f"w {int(e['wides'])}")
                        if e['noballs'] > 0: extras_parts.append(f"nb {int(e['noballs'])}")
                        if e['byes'] > 0: extras_parts.append(f"b {int(e['byes'])}")
                        if e['legbyes'] > 0: extras_parts.append(f"lb {int(e['legbyes'])}")
                        st.markdown(f"**Extras:** {int(e['total_extras'])} ({', '.join(extras_parts) if extras_parts else '0'})")

                    # Total
                    st.markdown(f"**Total:** {int(inn_total['total'])}/{int(inn_total['wickets'])} ({int(inn_total['overs'])}.{int(inn_total['last_ball'])} overs)")

                    st.markdown("---")

                    # BOWLING SCORECARD
                    st.markdown("##### Bowling")

                    bowling = run_query(f"""
                        SELECT
                            bowler as Bowler,
                            COUNT(*) as balls,
                            FLOOR(COUNT(*) / 6) || '.' || (COUNT(*) % 6) as O,
                            SUM(CASE WHEN total_runs = 0 AND extras_type IS NULL THEN 1 ELSE 0 END) as M,
                            SUM(total_runs) as R,
                            SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) as W,
                            ROUND(SUM(total_runs) * 6.0 / NULLIF(COUNT(*), 0), 2) as Econ
                        FROM stg_deliveries
                        WHERE match_id = '{selected_match}' AND innings = {innings}
                        GROUP BY bowler
                        ORDER BY MIN(over_number)
                    """)

                    # Calculate maidens properly (complete overs with 0 runs)
                    bowling_display = bowling[['Bowler', 'O', 'M', 'R', 'W', 'Econ']].copy()
                    bowling_display['R'] = bowling_display['R'].astype(int)
                    bowling_display['W'] = bowling_display['W'].astype(int)
                    bowling_display['M'] = 0  # Maiden calculation is complex, set to 0 for now

                    st.dataframe(bowling_display, use_container_width=True, hide_index=True)

                    # Fall of wickets
                    fow = run_query(f"""
                        SELECT
                            wicket_player_out as player,
                            (SELECT SUM(total_runs) FROM stg_deliveries d2
                             WHERE d2.match_id = d.match_id AND d2.innings = d.innings
                             AND (d2.over_number < d.over_number OR (d2.over_number = d.over_number AND d2.ball_number <= d.ball_number))) as score,
                            over_number || '.' || ball_number as over_ball,
                            ROW_NUMBER() OVER (ORDER BY over_number, ball_number) as wicket_num
                        FROM stg_deliveries d
                        WHERE match_id = '{selected_match}' AND innings = {innings} AND is_wicket
                        ORDER BY over_number, ball_number
                    """)

                    if len(fow) > 0:
                        st.markdown("##### Fall of Wickets")
                        fow_str = " • ".join([f"{int(row['score'])}/{int(row['wicket_num'])} ({row['player']}, {row['over_ball']})" for _, row in fow.iterrows()])
                        st.caption(fow_str)

# Head to Head page - combines Team vs Team, Player vs Player, Player vs Team, Player at Venue
elif page == "Head to Head":
    st.title("⚔️ Head to Head")

    tab1, tab2, tab3, tab4 = st.tabs(["Team vs Team", "Player vs Player", "Player vs Team", "Player at Venue"])

    with tab1:
        # Teams from team_metrics semantic model (normalize names)
        teams = run_query("""
            SELECT DISTINCT REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team
            FROM team_metrics ORDER BY team
        """)

        col1, col2 = st.columns(2)
        with col1:
            team1 = st.selectbox("Team 1", teams['team'].tolist())
        with col2:
            team2 = st.selectbox("Team 2", teams['team'].tolist(), index=1)

        if team1 and team2 and team1 != team2:
            # Show team stats from team_metrics (normalize for comparison)
            st.subheader("Team Statistics")
            team_stats = run_query(f"""
                SELECT
                    REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team,
                    matches_played, matches_won, win_percentage,
                    team_strike_rate, team_economy_rate
                FROM team_metrics
                WHERE REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') IN ('{team1}', '{team2}')
            """)

            col1, col2 = st.columns(2)
            for i, (idx, row) in enumerate(team_stats.iterrows()):
                with [col1, col2][i]:
                    display_team_logo(row['team'], size=100)
                    st.markdown(f"**{row['team']}**")
                    st.metric("Matches", row['matches_played'])
                    st.metric("Win %", f"{row['win_percentage']}%")
                    st.metric("Team SR", row['team_strike_rate'])

            st.divider()

            # Head to head from staging model (normalize team names for comparison)
            h2h = run_query(f"""
                WITH normalized AS (
                    SELECT
                        REPLACE(REPLACE(team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team1,
                        REPLACE(REPLACE(team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team2,
                        REPLACE(REPLACE(winner, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as winner
                    FROM stg_matches
                )
                SELECT
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN winner = '{team1}' THEN 1 ELSE 0 END) as team1_wins,
                    SUM(CASE WHEN winner = '{team2}' THEN 1 ELSE 0 END) as team2_wins,
                    SUM(CASE WHEN winner IS NULL OR (winner != '{team1}' AND winner != '{team2}') THEN 1 ELSE 0 END) as no_result
                FROM normalized
                WHERE (team1 = '{team1}' AND team2 = '{team2}')
                   OR (team1 = '{team2}' AND team2 = '{team1}')
            """)

            st.subheader("Head to Head Record")
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

            # Recent matches from staging model
            st.subheader("Recent Matches")
            recent = run_query(f"""
                WITH normalized AS (
                    SELECT
                        match_date, city, win_by_runs, win_by_wickets, player_of_match,
                        REPLACE(REPLACE(team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team1,
                        REPLACE(REPLACE(team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team2,
                        REPLACE(REPLACE(winner, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as winner
                    FROM stg_matches
                )
                SELECT match_date, city, winner,
                       CASE WHEN win_by_runs > 0 THEN win_by_runs || ' runs'
                            WHEN win_by_wickets > 0 THEN win_by_wickets || ' wickets'
                            ELSE 'N/A' END as margin,
                       player_of_match
                FROM normalized
                WHERE (team1 = '{team1}' AND team2 = '{team2}')
                   OR (team1 = '{team2}' AND team2 = '{team1}')
                ORDER BY match_date DESC
                LIMIT 10
            """)
            st.dataframe(recent, use_container_width=True, hide_index=True)

    with tab2:
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
            player1 = st.selectbox("Select Batter", batters['batter'].tolist(), key="p1")
        with col2:
            player2 = st.selectbox("Select Bowler", bowlers['bowler'].tolist(), key="p2")

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
                        photo_url = batter_info['photo_url'].iloc[0]
                        if photo_url and pd.notna(batter_info['key_cricinfo'].iloc[0]) and check_image_exists(photo_url):
                            st.image(photo_url, width=100)
                        elif PLAYER_PLACEHOLDER.exists():
                            st.image(str(PLAYER_PLACEHOLDER), width=100)
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
                        photo_url = bowler_info['photo_url'].iloc[0]
                        if photo_url and pd.notna(bowler_info['key_cricinfo'].iloc[0]) and check_image_exists(photo_url):
                            st.image(photo_url, width=100)
                        elif PLAYER_PLACEHOLDER.exists():
                            st.image(str(PLAYER_PLACEHOLDER), width=100)
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

    with tab3:
        st.caption("How a player performs against a specific team")

        col1, col2 = st.columns(2)

        with col1:
            players_t = run_query("""
                SELECT DISTINCT batter FROM batting_metrics
                WHERE total_runs >= 100
                ORDER BY batter
            """)
            selected_player_t = st.selectbox("Select Player", players_t['batter'].tolist(), key="pvt_player")

        with col2:
            teams_t = run_query("""
                SELECT DISTINCT REPLACE(REPLACE(team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') as team
                FROM team_metrics ORDER BY team
            """)
            selected_team_t = st.selectbox("Select Opposition Team", teams_t['team'].tolist())

        if selected_player_t and selected_team_t:
            player_info = run_query(f"""
                SELECT b.cricinfo_id
                FROM batting_metrics b
                WHERE b.batter = '{selected_player_t}'
            """)

            col1, col2 = st.columns([1, 3])
            with col1:
                if len(player_info) > 0 and pd.notna(player_info['cricinfo_id'].iloc[0]):
                    photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(player_info['cricinfo_id'].iloc[0])}.png"
                    if check_image_exists(photo_url):
                        st.image(photo_url, width=100)
                    elif PLAYER_PLACEHOLDER.exists():
                        st.image(str(PLAYER_PLACEHOLDER), width=100)
                elif PLAYER_PLACEHOLDER.exists():
                    st.image(str(PLAYER_PLACEHOLDER), width=100)

            with col2:
                st.markdown(f"### {selected_player_t}")
                display_team_logo(selected_team_t, size=50)
                st.caption(f"vs {selected_team_t}")

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
                  AND REPLACE(REPLACE(d.batting_team, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') != '{selected_team_t}'
                  AND (REPLACE(REPLACE(m.team1, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') = '{selected_team_t}'
                       OR REPLACE(REPLACE(m.team2, 'Royal Challengers Bangalore', 'Royal Challengers Bengaluru'), 'Rising Pune Supergiants', 'Rising Pune Supergiant') = '{selected_team_t}')
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

    with tab4:
        st.caption("How a player performs at different stadiums")

        col1, col2 = st.columns(2)

        with col1:
            players_v = run_query("""
                SELECT DISTINCT batter FROM batting_metrics
                WHERE total_runs >= 100
                ORDER BY batter
            """)
            selected_player_v = st.selectbox("Select Player", players_v['batter'].tolist(), key="venue_player")

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
                if len(player_info) > 0 and pd.notna(player_info['cricinfo_id'].iloc[0]):
                    photo_url = f"https://a.espncdn.com/i/headshots/cricket/players/full/{int(player_info['cricinfo_id'].iloc[0])}.png"
                    if check_image_exists(photo_url):
                        st.image(photo_url, width=100)
                    elif PLAYER_PLACEHOLDER.exists():
                        st.image(str(PLAYER_PLACEHOLDER), width=100)
                elif PLAYER_PLACEHOLDER.exists():
                    st.image(str(PLAYER_PLACEHOLDER), width=100)

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
            else:
                st.info(f"No batting data found for {selected_player_v} at {selected_venue}")

# Impact Players page
elif page == "Impact Players":
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

# SQL Query page
elif page == "SQL Query":
    st.title("🔍 SQL Query Editor")

    st.markdown("""
    **Available Tables (dbt Semantic Layer):**
    - `batting_metrics` - Aggregated batting stats (avg, SR, 50s, 100s)
    - `bowling_metrics` - Aggregated bowling stats (avg, economy, SR)
    - `team_metrics` - Team-level statistics
    - `stg_matches` - Staging matches data
    - `stg_deliveries` - Staging deliveries data
    - `metricflow_time_spine` - Time dimension table

    **Raw Tables:**
    - `matches` - Raw match data
    - `deliveries` - Raw ball-by-ball data
    - `people` - Player registry
    """)

    # Sample queries using semantic layer
    with st.expander("Sample Queries (Semantic Layer)"):
        st.code("""
-- Top 10 run scorers from batting_metrics
SELECT batter, total_runs, batting_average, strike_rate
FROM batting_metrics
ORDER BY total_runs DESC
LIMIT 10;

-- Top bowlers by economy from bowling_metrics
SELECT bowler, total_wickets, economy_rate, bowling_average
FROM bowling_metrics
WHERE total_wickets >= 50
ORDER BY economy_rate ASC
LIMIT 10;

-- Team performance from team_metrics
SELECT team, matches_played, matches_won, win_percentage
FROM team_metrics
ORDER BY win_percentage DESC;

-- Best all-rounders (runs + wickets)
SELECT b.batter as player, b.total_runs, bo.total_wickets
FROM batting_metrics b
JOIN bowling_metrics bo ON b.batter = bo.bowler
WHERE b.total_runs >= 1000 AND bo.total_wickets >= 50
ORDER BY b.total_runs + bo.total_wickets * 20 DESC
LIMIT 10;
        """, language="sql")

    # Query input
    query = st.text_area("Enter SQL Query", height=150, value="SELECT * FROM batting_metrics ORDER BY total_runs DESC LIMIT 10")

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

# Feedback page
elif page == "Feedback":
    st.title("📝 Feedback")
    st.markdown("We'd love to hear from you! Share your feedback, suggestions, or report any issues.")

    st.markdown("### [Click here to send feedback via email](mailto:gautamoncloud9@gmail.com?subject=IPL%20Explorer%20Feedback)")

    st.caption("Your feedback helps us improve the IPL Explorer app!")

# Footer
st.sidebar.divider()
st.sidebar.markdown("Data source: [Cricsheet](https://cricsheet.org)")
st.sidebar.markdown("Built with dbt semantic layer")
