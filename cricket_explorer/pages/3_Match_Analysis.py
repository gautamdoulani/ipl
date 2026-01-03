"""Cricket Data Explorer - Match Analysis/Scorecard page."""

import streamlit as st
import pandas as pd
from config import get_team_replacement_sql, apply_team_replacements
from utils import run_query, display_team_logo


# Get query params for direct navigation
match_id_param = st.query_params.get('match_id', '')
season_param = st.query_params.get('season', '')

# Convert to proper types
pre_selected_match = None
pre_selected_season = None
if match_id_param:
    try:
        pre_selected_match = int(match_id_param)
    except ValueError:
        pass
if season_param:
    pre_selected_season = season_param

st.title("📊 Match Scorecard")

# Season and match selection from staging model
seasons = run_query("SELECT DISTINCT season FROM stg_matches WHERE season IS NOT NULL ORDER BY season DESC")
season_list = [str(s) for s in seasons['season'].tolist()]

# Pre-select season if coming from query params
default_season_idx = 0
if pre_selected_season and pre_selected_season in season_list:
    default_season_idx = season_list.index(pre_selected_season)

selected_season = st.selectbox("Select Season", season_list, index=default_season_idx)

team1_sql = get_team_replacement_sql("team1")
team2_sql = get_team_replacement_sql("team2")
batting_team_sql = get_team_replacement_sql("batting_team")
winner_sql = get_team_replacement_sql("winner")
toss_winner_sql = get_team_replacement_sql("toss_winner")

matches = run_query(f"""
    SELECT match_id, match_date,
           {team1_sql} || ' vs ' || {team2_sql} as match_name,
           city
    FROM stg_matches
    WHERE season = '{selected_season}'
    ORDER BY match_date DESC
""")

match_options = dict(zip(matches['match_id'].astype(int), matches['match_name'] + ' (' + matches['match_date'].astype(str) + ')'))
match_list = list(match_options.keys())

# Pre-select match if coming from query params
default_match_idx = 0
if pre_selected_match and pre_selected_match in match_list:
    default_match_idx = match_list.index(pre_selected_match)

selected_match = st.selectbox("Select Match", match_list, index=default_match_idx, format_func=lambda x: match_options[x])

if selected_match:
    # Update URL with current selection
    st.query_params['match_id'] = str(selected_match)
    st.query_params['season'] = selected_season

    # Match details from staging model
    match_info = run_query(f"""
        SELECT * FROM stg_matches WHERE match_id = '{selected_match}'
    """)

    # Get innings totals for header
    innings_totals = run_query(f"""
        SELECT
            innings,
            {batting_team_sql} as batting_team,
            SUM(total_runs) as total,
            SUM(CASE WHEN is_wicket THEN 1 ELSE 0 END) as wickets,
            SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END) as legal_balls
        FROM stg_deliveries
        WHERE match_id = '{selected_match}'
        GROUP BY innings, {batting_team_sql}
        ORDER BY innings
    """)

    # Match Header with team scores
    st.divider()
    header_cols = st.columns([2, 1, 2])

    team1_data = innings_totals[innings_totals['innings'] == 1].iloc[0] if len(innings_totals) > 0 else None
    team2_data = innings_totals[innings_totals['innings'] == 2].iloc[0] if len(innings_totals) > 1 else None

    with header_cols[0]:
        if team1_data is not None:
            display_team_logo(team1_data['batting_team'], size=60)
            st.markdown(f"### {team1_data['batting_team']}")
            legal_balls = int(team1_data['legal_balls'])
            overs_str = f"{legal_balls // 6}.{legal_balls % 6}"
            st.markdown(f"## {int(team1_data['total'])}/{int(team1_data['wickets'])}")
            st.caption(f"({overs_str} overs)")

    with header_cols[1]:
        st.markdown("<div style='text-align: center; padding-top: 30px;'><h3>vs</h3></div>", unsafe_allow_html=True)

    with header_cols[2]:
        if team2_data is not None:
            display_team_logo(team2_data['batting_team'], size=60)
            st.markdown(f"### {team2_data['batting_team']}")
            legal_balls = int(team2_data['legal_balls'])
            overs_str = f"{legal_balls // 6}.{legal_balls % 6}"
            st.markdown(f"## {int(team2_data['total'])}/{int(team2_data['wickets'])}")
            st.caption(f"({overs_str} overs)")

    # Result (normalize team name)
    winner_raw = match_info['winner'].iloc[0]
    winner = apply_team_replacements(winner_raw) if winner_raw else None
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
    toss_winner_raw = match_info['toss_winner'].iloc[0]
    toss_winner = apply_team_replacements(toss_winner_raw) if toss_winner_raw else 'N/A'
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption(f"**Venue:** {match_info['venue'].iloc[0] or match_info['city'].iloc[0] or 'N/A'}")
    with col2:
        st.caption(f"**Date:** {match_info['match_date'].iloc[0]}")
    with col3:
        st.caption(f"**Toss:** {toss_winner} ({match_info['toss_decision'].iloc[0]})")
    with col4:
        st.caption(f"**Player of Match:** {match_info['player_of_match'].iloc[0] or 'N/A'}")

    st.divider()

    # Innings scorecards
    for innings in [1, 2]:
        innings_data = run_query(f"""
            SELECT {batting_team_sql} as batting_team
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

                st.dataframe(batting_display, width="stretch", hide_index=True)

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
                legal_balls_inn = int(inn_total['legal_balls'])
                overs_inn_str = f"{legal_balls_inn // 6}.{legal_balls_inn % 6}"
                st.markdown(f"**Total:** {int(inn_total['total'])}/{int(inn_total['wickets'])} ({overs_inn_str} overs)")

                st.divider()

                # BOWLING SCORECARD
                st.markdown("##### Bowling")

                bowling = run_query(f"""
                    SELECT
                        bowler as Bowler,
                        SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END) as legal_balls,
                        CAST(FLOOR(SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END) / 6) AS INTEGER) || '.' ||
                            (SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END) % 6) as O,
                        SUM(CASE WHEN total_runs = 0 AND extras_type IS NULL THEN 1 ELSE 0 END) as M,
                        SUM(total_runs) as R,
                        SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) as W,
                        ROUND(SUM(total_runs) * 6.0 / NULLIF(SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END), 0), 2) as Econ
                    FROM stg_deliveries
                    WHERE match_id = '{selected_match}' AND innings = {innings}
                    GROUP BY bowler
                    ORDER BY MIN(over_number)
                """)

                bowling_display = bowling[['Bowler', 'O', 'M', 'R', 'W', 'Econ']].copy()
                bowling_display['R'] = bowling_display['R'].astype(int)
                bowling_display['W'] = bowling_display['W'].astype(int)
                bowling_display['M'] = 0  # Maiden calculation is complex, set to 0 for now

                st.dataframe(bowling_display, width="stretch", hide_index=True)

                # Fall of wickets
                fow = run_query(f"""
                    WITH legal_balls_numbered AS (
                        SELECT *,
                            SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END)
                                OVER (ORDER BY over_number, ball_number) as cumulative_legal_balls
                        FROM stg_deliveries
                        WHERE match_id = '{selected_match}' AND innings = {innings}
                    )
                    SELECT
                        wicket_player_out as player,
                        (SELECT SUM(total_runs) FROM stg_deliveries d2
                         WHERE d2.match_id = '{selected_match}' AND d2.innings = {innings}
                         AND (d2.over_number < d.over_number OR (d2.over_number = d.over_number AND d2.ball_number <= d.ball_number))) as score,
                        CAST(FLOOR((cumulative_legal_balls - 1) / 6) AS INTEGER) || '.' || ((cumulative_legal_balls - 1) % 6 + 1) as over_ball,
                        ROW_NUMBER() OVER (ORDER BY over_number, ball_number) as wicket_num
                    FROM legal_balls_numbered d
                    WHERE is_wicket
                    ORDER BY over_number, ball_number
                """)

                if len(fow) > 0:
                    st.markdown("##### Fall of Wickets")
                    fow_str = " • ".join([f"{int(row['score'])}/{int(row['wicket_num'])} ({row['player']}, {row['over_ball']})" for _, row in fow.iterrows()])
                    st.caption(fow_str)
