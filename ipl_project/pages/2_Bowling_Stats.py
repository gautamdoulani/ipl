"""IPL Data Explorer - Bowling Statistics page."""

import streamlit as st
from utils import run_query, display_player_cards


st.title("🎳 Bowling Statistics")

# Season filter
seasons_df = run_query("SELECT DISTINCT season FROM stg_matches ORDER BY season DESC")
all_seasons = seasons_df['season'].tolist()

selected_seasons = st.multiselect(
    "Select Seasons",
    options=all_seasons,
    default=[],
    placeholder="All Seasons"
)

# Build season filter clause
if selected_seasons:
    season_list = ", ".join(f"'{s}'" for s in selected_seasons)
    season_filter = f"AND season IN ({season_list})"
    st.caption(f"Showing data for: {', '.join(selected_seasons)}")
else:
    season_filter = ""
    st.caption("Showing data for: All Seasons")

st.divider()

# Top Wicket Takers Section
st.subheader("Top Wicket Takers")
col1, col2 = st.columns(2)
with col1:
    min_wickets = st.slider("Minimum Wickets", 0, 100, 10, key="top_wickets_min")
with col2:
    min_matches_bowl = st.slider("Minimum Matches", 1, 100, 10, key="top_wickets_matches")

bowling = run_query(f"""
    WITH bowling_innings AS (
        SELECT
            d.match_id,
            d.bowler,
            d.bowler_cricinfo_id,
            SUM(d.total_runs) as runs_conceded,
            COUNT(CASE WHEN d.extras_type IS NULL OR (d.extras_type NOT LIKE '%wides%' AND d.extras_type NOT LIKE '%noballs%') THEN 1 END) as balls_bowled,
            SUM(CASE
                WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field')
                THEN 1 ELSE 0
            END) as wickets
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.match_id, d.bowler, d.bowler_cricinfo_id
    ),
    bowling_agg AS (
        SELECT
            bowler,
            MAX(bowler_cricinfo_id) as cricinfo_id,
            COUNT(DISTINCT match_id) as matches,
            COUNT(*) as innings,
            SUM(runs_conceded) as total_runs_conceded,
            SUM(balls_bowled) as total_balls,
            SUM(wickets) as total_wickets,
            MAX(wickets) as best_wickets_innings,
            SUM(CASE WHEN wickets = 4 THEN 1 ELSE 0 END) as four_wickets,
            SUM(CASE WHEN wickets >= 5 THEN 1 ELSE 0 END) as five_wickets
        FROM bowling_innings
        GROUP BY bowler
    ),
    best_figures AS (
        SELECT
            bowler,
            wickets as best_wickets,
            runs_conceded as best_runs,
            ROW_NUMBER() OVER (PARTITION BY bowler ORDER BY wickets DESC, runs_conceded ASC) as rn
        FROM bowling_innings
    )
    SELECT
        ba.bowler,
        ba.cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || ba.cricinfo_id || '.png' as photo_url,
        ba.matches,
        ba.innings,
        CAST(FLOOR(ba.total_balls / 6) AS INTEGER) || '.' || (ba.total_balls % 6) as overs,
        ba.total_wickets as wickets,
        ba.total_runs_conceded as runs,
        ROUND(ba.total_runs_conceded * 1.0 / NULLIF(ba.total_wickets, 0), 2) as average,
        ROUND(ba.total_runs_conceded * 6.0 / NULLIF(ba.total_balls, 0), 2) as economy,
        ROUND(ba.total_balls * 1.0 / NULLIF(ba.total_wickets, 0), 2) as strike_rate,
        bf.best_wickets || '/' || bf.best_runs as best_bowling,
        ba.four_wickets as "4W",
        ba.five_wickets as "5W"
    FROM bowling_agg ba
    LEFT JOIN best_figures bf ON ba.bowler = bf.bowler AND bf.rn = 1
    WHERE ba.total_wickets >= {min_wickets} AND ba.matches >= {min_matches_bowl}
    ORDER BY wickets DESC
    LIMIT 20
""")

if len(bowling) > 0:
    display_player_cards(bowling, 'bowler', 'wickets', 'Wickets', limit=5)
    st.divider()
    display_cols = [c for c in bowling.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(bowling[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.divider()

# Most Wicket Hauls Section
st.subheader("Most Wicket Hauls")
st.caption("4-wicket and 5-wicket hauls in an innings")

wicket_hauls = run_query(f"""
    WITH bowling_innings AS (
        SELECT
            d.bowler,
            d.bowler_cricinfo_id,
            d.match_id,
            SUM(CASE
                WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field')
                THEN 1 ELSE 0
            END) as wickets
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.match_id, d.bowler, d.bowler_cricinfo_id
    )
    SELECT
        bowler,
        MAX(bowler_cricinfo_id) as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || MAX(bowler_cricinfo_id) || '.png' as photo_url,
        SUM(CASE WHEN wickets = 4 THEN 1 ELSE 0 END) as "4W",
        SUM(CASE WHEN wickets >= 5 THEN 1 ELSE 0 END) as "5W",
        SUM(CASE WHEN wickets >= 4 THEN 1 ELSE 0 END) as total_hauls
    FROM bowling_innings
    GROUP BY bowler
    HAVING SUM(CASE WHEN wickets >= 4 THEN 1 ELSE 0 END) > 0
    ORDER BY total_hauls DESC, "5W" DESC
    LIMIT 15
""")
if len(wicket_hauls) > 0:
    display_player_cards(wicket_hauls, 'bowler', 'total_hauls', 'Hauls', limit=5)
    st.divider()
    display_cols = [c for c in wicket_hauls.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(wicket_hauls[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No wicket hauls found for selected seasons")

st.divider()

# Best Economy Rates Section
st.subheader("Best Economy Rates")
econ_min_wickets = st.slider("Minimum Wickets for Economy", 10, 150, 50, key="econ_min_wickets")

economy = run_query(f"""
    WITH bowling_agg AS (
        SELECT
            d.bowler,
            d.bowler_cricinfo_id as cricinfo_id,
            SUM(d.total_runs) as total_runs_conceded,
            COUNT(*) as total_balls,
            SUM(CASE
                WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field')
                THEN 1 ELSE 0
            END) as total_wickets
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.bowler, d.bowler_cricinfo_id
    )
    SELECT
        bowler,
        cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
        CAST(FLOOR(total_balls / 6) AS INTEGER) || '.' || (total_balls % 6) as overs,
        total_runs_conceded as runs,
        ROUND(total_runs_conceded * 6.0 / NULLIF(total_balls, 0), 2) as economy
    FROM bowling_agg
    WHERE total_wickets >= {econ_min_wickets}
    ORDER BY economy ASC
    LIMIT 15
""")
if len(economy) > 0:
    display_player_cards(economy, 'bowler', 'economy', 'Econ', limit=5)
    st.divider()
    display_cols = [c for c in economy.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(economy[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.divider()

# Best Bowling Averages Section
st.subheader("Best Bowling Averages")
avg_min_wickets = st.slider("Minimum Wickets for Average", 10, 150, 50, key="avg_min_wickets")

bowl_avg = run_query(f"""
    WITH bowling_agg AS (
        SELECT
            d.bowler,
            d.bowler_cricinfo_id as cricinfo_id,
            SUM(d.total_runs) as total_runs_conceded,
            SUM(CASE
                WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field')
                THEN 1 ELSE 0
            END) as total_wickets
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.bowler, d.bowler_cricinfo_id
    )
    SELECT
        bowler,
        cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
        total_runs_conceded as runs,
        total_wickets as wickets,
        ROUND(total_runs_conceded * 1.0 / NULLIF(total_wickets, 0), 2) as average
    FROM bowling_agg
    WHERE total_wickets >= {avg_min_wickets}
    ORDER BY average ASC
    LIMIT 15
""")
if len(bowl_avg) > 0:
    display_player_cards(bowl_avg, 'bowler', 'average', 'Avg', limit=5)
    st.divider()
    display_cols = [c for c in bowl_avg.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(bowl_avg[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.divider()

# Best Bowling Strike Rates Section
st.subheader("Best Bowling Strike Rates")
st.caption("Balls per wicket - lower is better")
sr_min_wickets = st.slider("Minimum Wickets for Strike Rate", 10, 150, 50, key="sr_min_wickets")

bowl_sr = run_query(f"""
    WITH bowling_agg AS (
        SELECT
            d.bowler,
            d.bowler_cricinfo_id as cricinfo_id,
            COUNT(*) as total_balls,
            SUM(CASE
                WHEN d.is_wicket AND d.wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field')
                THEN 1 ELSE 0
            END) as total_wickets
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.bowler, d.bowler_cricinfo_id
    )
    SELECT
        bowler,
        cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
        total_balls as balls,
        total_wickets as wickets,
        ROUND(total_balls * 1.0 / NULLIF(total_wickets, 0), 2) as strike_rate
    FROM bowling_agg
    WHERE total_wickets >= {sr_min_wickets}
    ORDER BY strike_rate ASC
    LIMIT 15
""")
if len(bowl_sr) > 0:
    display_player_cards(bowl_sr, 'bowler', 'strike_rate', 'SR', limit=5)
    st.divider()
    display_cols = [c for c in bowl_sr.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(bowl_sr[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")
