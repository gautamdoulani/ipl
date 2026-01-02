"""IPL Data Explorer - SQL Query Editor."""

import streamlit as st
from utils import run_query


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
