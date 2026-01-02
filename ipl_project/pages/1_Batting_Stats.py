"""IPL Data Explorer - Batting Statistics page."""

import streamlit as st
from utils import run_query, display_player_cards


st.title("🏏 Batting Statistics")

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

# Top Run Scorers Section
st.subheader("Top Run Scorers")
col1, col2 = st.columns(2)
with col1:
    min_runs = st.slider("Minimum Runs", 0, 2000, 100, key="top_runs_min")
with col2:
    min_matches = st.slider("Minimum Matches", 1, 100, 10, key="top_runs_matches")

batting = run_query(f"""
    WITH batting_agg AS (
        SELECT
            d.batter,
            d.batter_cricinfo_id as cricinfo_id,
            COUNT(DISTINCT d.match_id) as matches,
            COUNT(DISTINCT CASE WHEN d.batter = d.batter THEN d.match_id || '-' || d.innings END) as innings,
            SUM(d.batter_runs) as total_runs,
            COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%' THEN 1 END) as total_balls,
            SUM(CASE WHEN d.batter_runs = 4 THEN 1 ELSE 0 END) as total_fours,
            SUM(CASE WHEN d.batter_runs = 6 THEN 1 ELSE 0 END) as total_sixes,
            SUM(CASE WHEN d.is_wicket AND d.wicket_player_out = d.batter THEN 1 ELSE 0 END) as dismissals
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.batter, d.batter_cricinfo_id
    ),
    innings_scores AS (
        SELECT
            d.batter,
            d.match_id,
            d.innings,
            SUM(d.batter_runs) as innings_runs
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.batter, d.match_id, d.innings
    ),
    milestones AS (
        SELECT
            batter,
            MAX(innings_runs) as highest_score,
            SUM(CASE WHEN innings_runs >= 50 AND innings_runs < 100 THEN 1 ELSE 0 END) as fifties,
            SUM(CASE WHEN innings_runs >= 100 THEN 1 ELSE 0 END) as centuries
        FROM innings_scores
        GROUP BY batter
    )
    SELECT
        b.batter,
        b.cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || b.cricinfo_id || '.png' as photo_url,
        b.matches,
        b.innings,
        b.total_runs as runs,
        b.total_balls as balls,
        ROUND(b.total_runs * 1.0 / NULLIF(b.dismissals, 0), 2) as average,
        ROUND(b.total_runs * 100.0 / NULLIF(b.total_balls, 0), 2) as strike_rate,
        b.total_fours as fours,
        b.total_sixes as sixes,
        m.fifties,
        m.centuries,
        m.highest_score
    FROM batting_agg b
    LEFT JOIN milestones m ON b.batter = m.batter
    WHERE b.total_runs >= {min_runs} AND b.matches >= {min_matches}
    ORDER BY runs DESC
    LIMIT 20
""")

if len(batting) > 0:
    display_player_cards(batting, 'batter', 'runs', 'Runs', limit=5)
    st.divider()
    display_cols = [c for c in batting.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(batting[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.divider()

# Best Strike Rates Section
st.subheader("Best Strike Rates")
sr_min_runs = st.slider("Minimum Runs for Strike Rate", 100, 2000, 500, key="sr_min_runs")

strike_rates = run_query(f"""
    WITH batting_agg AS (
        SELECT
            d.batter,
            d.batter_cricinfo_id as cricinfo_id,
            SUM(d.batter_runs) as total_runs,
            COUNT(CASE WHEN d.extras_type IS NULL OR d.extras_type NOT LIKE '%wides%' THEN 1 END) as total_balls
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.batter, d.batter_cricinfo_id
    )
    SELECT
        batter,
        cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
        total_runs as runs,
        total_balls as balls,
        ROUND(total_runs * 100.0 / NULLIF(total_balls, 0), 2) as strike_rate
    FROM batting_agg
    WHERE total_runs >= {sr_min_runs}
    ORDER BY strike_rate DESC
    LIMIT 15
""")
if len(strike_rates) > 0:
    display_player_cards(strike_rates, 'batter', 'strike_rate', 'SR', limit=5)
    st.divider()
    display_cols = [c for c in strike_rates.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(strike_rates[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.divider()

# Best Averages Section
st.subheader("Best Batting Averages")
avg_min_runs = st.slider("Minimum Runs for Average", 100, 2000, 500, key="avg_min_runs")

averages = run_query(f"""
    WITH batting_agg AS (
        SELECT
            d.batter,
            d.batter_cricinfo_id as cricinfo_id,
            SUM(d.batter_runs) as total_runs,
            SUM(CASE WHEN d.is_wicket AND d.wicket_player_out = d.batter THEN 1 ELSE 0 END) as dismissals
        FROM stg_deliveries d
        WHERE 1=1 {season_filter}
        GROUP BY d.batter, d.batter_cricinfo_id
    )
    SELECT
        batter,
        cricinfo_id as key_cricinfo,
        'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
        total_runs as runs,
        dismissals,
        ROUND(total_runs * 1.0 / NULLIF(dismissals, 0), 2) as average
    FROM batting_agg
    WHERE total_runs >= {avg_min_runs}
    ORDER BY average DESC
    LIMIT 15
""")
if len(averages) > 0:
    display_player_cards(averages, 'batter', 'average', 'Avg', limit=5)
    st.divider()
    display_cols = [c for c in averages.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(averages[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")
