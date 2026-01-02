"""IPL Data Explorer - Bowling Statistics page."""

import streamlit as st
from utils import run_query, display_player_cards


st.title("🎳 Bowling Statistics")
st.caption("Data from dbt semantic layer: bowling_metrics")

# Top Wicket Takers Section
st.subheader("Top Wicket Takers")
col1, col2 = st.columns(2)
with col1:
    min_wickets = st.slider("Minimum Wickets", 0, 100, 10, key="top_wickets_min")
with col2:
    min_matches_bowl = st.slider("Minimum Matches", 1, 100, 10, key="top_wickets_matches")

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

if len(bowling) > 0:
    display_player_cards(bowling, 'bowler', 'wickets', 'Wickets', limit=5)
    st.divider()
    display_cols = [c for c in bowling.columns if c not in ['key_cricinfo', 'photo_url']]
    st.dataframe(bowling[display_cols], use_container_width=True, hide_index=True)
else:
    st.info("No players match the criteria")

st.markdown("---")

# Best Economy Rates Section
st.subheader("Best Economy Rates")
econ_min_wickets = st.slider("Minimum Wickets for Economy", 10, 150, 50, key="econ_min_wickets")

economy = run_query(f"""
    SELECT bowler,
           cricinfo_id as key_cricinfo,
           'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
           total_wickets as wickets, overs, economy_rate as economy
    FROM bowling_metrics
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

st.markdown("---")

# Best Bowling Averages Section
st.subheader("Best Bowling Averages")
avg_min_wickets = st.slider("Minimum Wickets for Average", 10, 150, 50, key="avg_min_wickets")

bowl_avg = run_query(f"""
    SELECT bowler,
           cricinfo_id as key_cricinfo,
           'https://a.espncdn.com/i/headshots/cricket/players/full/' || cricinfo_id || '.png' as photo_url,
           total_wickets as wickets, total_runs_conceded as runs, bowling_average as average
    FROM bowling_metrics
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
