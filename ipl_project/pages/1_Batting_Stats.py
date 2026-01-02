"""IPL Data Explorer - Batting Statistics page."""

import streamlit as st
from utils import run_query, display_player_cards


st.title("🏏 Batting Statistics")
st.caption("Data from dbt semantic layer: batting_metrics")

# Top Run Scorers Section
st.subheader("Top Run Scorers")
col1, col2 = st.columns(2)
with col1:
    min_runs = st.slider("Minimum Runs", 0, 2000, 100, key="top_runs_min")
with col2:
    min_matches = st.slider("Minimum Matches", 1, 100, 10, key="top_runs_matches")

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

if len(batting) > 0:
    display_player_cards(batting, 'batter', 'runs', 'Runs', limit=5)
    st.divider()
    display_cols = [c for c in batting.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(batting[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.markdown("---")

# Best Strike Rates Section
st.subheader("Best Strike Rates")
sr_min_runs = st.slider("Minimum Runs for Strike Rate", 100, 2000, 500, key="sr_min_runs")

strike_rates = run_query(f"""
    SELECT batter,
           cricinfo_id as key_cricinfo,
           'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
           total_runs as runs, total_balls as balls, strike_rate
    FROM batting_metrics
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

st.markdown("---")

# Best Averages Section
st.subheader("Best Batting Averages")
avg_min_runs = st.slider("Minimum Runs for Average", 100, 2000, 500, key="avg_min_runs")

averages = run_query(f"""
    SELECT batter,
           cricinfo_id as key_cricinfo,
           'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
           total_runs as runs, dismissals, batting_average as average
    FROM batting_metrics
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
