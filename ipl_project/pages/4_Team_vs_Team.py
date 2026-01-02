"""IPL Data Explorer - Team vs Team comparison."""

import streamlit as st
from utils import run_query, display_team_logo


st.title("⚔️ Team vs Team")

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
