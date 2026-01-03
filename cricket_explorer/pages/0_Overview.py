"""Cricket Data Explorer - Overview/Home page."""

import streamlit as st
from config import CONFIG, get_team_replacement_sql
from utils import run_query, display_team_logo, get_responsive_columns

st.title(f"🏏 {CONFIG['display_name']}")

# Build team replacement SQL for this league
team1_sql = get_team_replacement_sql("team1")
team2_sql = get_team_replacement_sql("team2")
winner_sql = get_team_replacement_sql("winner")

# Get final match of each season from staging model
winners = run_query(f"""
    WITH finals AS (
        SELECT
            season,
            match_id,
            match_date,
            {team1_sql} as team1,
            {team2_sql} as team2,
            {winner_sql} as winner,
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
trophy_count = run_query(f"""
    WITH finals AS (
        SELECT season,
               {winner_sql} as winner,
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

# Display as columns with team logos and trophy emoji - responsive
num_teams = len(trophy_count)
num_cols = get_responsive_columns(num_teams, max_desktop=7, max_tablet=4, max_mobile=2)
cols = st.columns(num_cols)
for i, (_, row) in enumerate(trophy_count.iterrows()):
    with cols[i % num_cols]:
        st.markdown('<div class="trophy-item">', unsafe_allow_html=True)
        display_team_logo(row['team'], size=80)
        trophies = "🏆" * row['titles']
        st.markdown(f"**{row['team']}**")
        st.markdown(f"{trophies}")
        st.caption(f"{row['years']}")
        st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Full winners table with link to match analysis
st.subheader("Season-wise Champions")

# Build display dataframe with clickable scorecard links
display_df = winners[['Season', 'Champion', 'Runner-up', 'Victory Margin', 'Finals MVP', 'Venue', 'match_id']].copy()

# Create clickable links to Match Analysis page
display_df['Scorecard'] = display_df.apply(
    lambda row: f"[📊 View](/Match_Analysis?match_id={row['match_id']}&season={row['Season']})",
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

team_season_perf = run_query(f"""
    WITH team_season AS (
        SELECT
            season,
            {team1_sql} as team,
            CASE WHEN {winner_sql} = {team1_sql} THEN 1 ELSE 0 END as won
        FROM stg_matches
        WHERE winner IS NOT NULL
        UNION ALL
        SELECT
            season,
            {team2_sql} as team,
            CASE WHEN {winner_sql} = {team2_sql} THEN 1 ELSE 0 END as won
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
    for _, row in winners.iterrows():
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
            val = matrix.loc[team, season]
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

            if (team, season) in champions:
                style += '; outline: 3px solid #FFD700; outline-offset: -3px'

            styles.append(style)
        return styles

    def format_cell(v, team, season):
        if v == -1:
            return '-'
        if (team, season) in champions:
            return f"🏆{int(v)}%"
        return f"{int(v)}%"

    formatted = matrix.copy().astype(object)
    for team in formatted.index:
        for season in formatted.columns:
            formatted.loc[team, season] = format_cell(matrix.loc[team, season], team, season)

    table_height = (len(matrix) + 1) * 35 + 10
    st.markdown('<p class="scroll-hint">↔️ Scroll horizontally on mobile to see all seasons</p>', unsafe_allow_html=True)
    styled_formatted = formatted.style.apply(style_matrix_with_champions, axis=1)
    st.dataframe(styled_formatted, width="stretch", height=table_height)

    st.caption("🟢 60%+ | 🟡 50-59% | 🟠 40-49% | 🔴 <40% | 🏆 = Championship winner")
