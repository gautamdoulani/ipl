"""Cricket Data Explorer - Team vs Team comparison."""

import streamlit as st
import base64
from config import get_team_replacement_sql
from utils import run_query, display_team_logo, get_team_logo_path


@st.cache_data
def get_all_teams():
    team_sql = get_team_replacement_sql("team")
    return run_query(f"""
        SELECT {team_sql} as team,
               matches_played
        FROM team_metrics
        ORDER BY matches_played DESC
    """)


st.title("⚔️ Team vs Team")

team_sql = get_team_replacement_sql("team")
team1_sql = get_team_replacement_sql("team1")
team2_sql = get_team_replacement_sql("team2")
winner_sql = get_team_replacement_sql("winner")

# Teams from team_metrics semantic model (cached)
teams = get_all_teams()

col1, col2 = st.columns(2)
with col1:
    team1 = st.selectbox("Team 1", teams['team'].tolist())
with col2:
    team2 = st.selectbox("Team 2", teams['team'].tolist(), index=1)

if team1 and team2 and team1 != team2:
    # Show team stats from team_metrics (normalize for comparison)
    st.subheader("Team Statistics")
    team_stats = run_query(f"""
        WITH normalized AS (
            SELECT
                {team_sql} as team,
                matches_played, matches_won, win_percentage,
                team_strike_rate, team_economy_rate
            FROM team_metrics
        )
        SELECT * FROM normalized
        WHERE team IN ('{team1}', '{team2}')
    """)

    # Display teams in the order selected by user (team1, team2)
    col1, col2 = st.columns(2)
    for i, selected_team in enumerate([team1, team2]):
        team_row = team_stats[team_stats['team'] == selected_team]
        with [col1, col2][i]:
            display_team_logo(selected_team, size=100)
            st.markdown(f"**{selected_team}**")
            if len(team_row) > 0:
                row = team_row.iloc[0]
                st.metric("Matches", row['matches_played'])
                st.metric("Win %", f"{row['win_percentage']}%")
                st.metric("Team SR", row['team_strike_rate'])
            else:
                st.caption("No stats available")

    st.divider()

    # Head to head from staging model (normalize team names for comparison)
    h2h = run_query(f"""
        WITH normalized AS (
            SELECT
                {team1_sql} as team1,
                {team2_sql} as team2,
                {winner_sql} as winner
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
        st.metric("Total Matches", int(h2h['total_matches'].iloc[0]))
    with col2:
        st.metric(f"{team1} Wins", int(h2h['team1_wins'].iloc[0]))
    with col3:
        st.metric(f"{team2} Wins", int(h2h['team2_wins'].iloc[0]))
    with col4:
        st.metric("No Result", int(h2h['no_result'].iloc[0]))

    # Last 10 matches visualization with team logos
    last_10 = run_query(f"""
        WITH normalized AS (
            SELECT
                match_date,
                {team1_sql} as team1,
                {team2_sql} as team2,
                {winner_sql} as winner
            FROM stg_matches
        )
        SELECT match_date, winner
        FROM normalized
        WHERE (team1 = '{team1}' AND team2 = '{team2}')
           OR (team1 = '{team2}' AND team2 = '{team1}')
        ORDER BY match_date DESC
        LIMIT 10
    """)

    if len(last_10) > 0:
        st.markdown("**Last 10 Matches**")

        # Load team logos as base64
        def get_logo_base64(team_name):
            logo_path = get_team_logo_path(team_name)
            if logo_path:
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            return None

        team1_logo = get_logo_base64(team1)
        team2_logo = get_logo_base64(team2)

        logos_html = []
        for _, row in last_10.iterrows():
            date_str = str(row['match_date'])
            if row['winner'] == team1 and team1_logo:
                logos_html.append(
                    f'<div style="display:flex; flex-direction:column; align-items:center; margin:0 4px;" title="{date_str}: {team1} won">'
                    f'<img src="data:image/png;base64,{team1_logo}" style="width:36px; height:36px; object-fit:contain; border-radius:4px; border:2px solid #28a745;">'
                    f'<span style="font-size:9px; color:#666; margin-top:2px;">{date_str[:4]}</span>'
                    f'</div>'
                )
            elif row['winner'] == team2 and team2_logo:
                logos_html.append(
                    f'<div style="display:flex; flex-direction:column; align-items:center; margin:0 4px;" title="{date_str}: {team2} won">'
                    f'<img src="data:image/png;base64,{team2_logo}" style="width:36px; height:36px; object-fit:contain; border-radius:4px; border:2px solid #dc3545;">'
                    f'<span style="font-size:9px; color:#666; margin-top:2px;">{date_str[:4]}</span>'
                    f'</div>'
                )
            else:
                logos_html.append(
                    f'<div style="display:flex; flex-direction:column; align-items:center; margin:0 4px;" title="{date_str}: No Result">'
                    f'<div style="width:36px; height:36px; background:#e0e0e0; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; color:#666;">N/R</div>'
                    f'<span style="font-size:9px; color:#666; margin-top:2px;">{date_str[:4]}</span>'
                    f'</div>'
                )

        # Reverse to show oldest to newest (left to right)
        logos_html.reverse()
        st.markdown(
            f'<div style="display:flex; align-items:flex-start; gap:4px; padding:10px 0;">'
            f'<span style="font-size:11px; color:#888; writing-mode:vertical-rl; transform:rotate(180deg); margin-right:8px;">← Oldest</span>'
            f'{"".join(logos_html)}'
            f'<span style="font-size:11px; color:#888; writing-mode:vertical-rl; transform:rotate(180deg); margin-left:8px;">Latest →</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Recent matches from staging model
    st.subheader("Recent Matches")
    recent = run_query(f"""
        WITH normalized AS (
            SELECT
                match_id, season, match_date, city, win_by_runs, win_by_wickets, player_of_match,
                {team1_sql} as team1,
                {team2_sql} as team2,
                {winner_sql} as winner
            FROM stg_matches
        )
        SELECT match_id, season, match_date, city, winner,
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

    # Add scorecard links
    recent['Scorecard'] = recent.apply(
        lambda row: f"/Match_Analysis?match_id={int(row['match_id'])}&season={row['season']}",
        axis=1
    )
    display_cols = ['match_date', 'city', 'winner', 'margin', 'player_of_match', 'Scorecard']
    st.dataframe(
        recent[display_cols],
        width="stretch",
        hide_index=True,
        column_config={
            "Scorecard": st.column_config.LinkColumn("Scorecard", display_text="View")
        }
    )
