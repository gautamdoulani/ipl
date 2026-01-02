"""IPL Data Explorer - SQL Query Editor."""

import streamlit as st
from utils import run_query


st.title("🔍 SQL Query Editor")

# Table Relationships Diagram
with st.expander("📊 Table Relationships", expanded=False):
    st.markdown("""
    ```
    ┌───────────────────────────────────────────────────────────────────┐
    │                      TABLE RELATIONSHIPS                          │
    ├───────────────────────────────────────────────────────────────────┤
    │                                                                   │
    │  ┌──────────────┐         ┌────────────────┐                     │
    │  │  stg_matches │◀────────│ stg_deliveries │                     │
    │  └──────────────┘         └────────────────┘                     │
    │   (match_id,               (match_id,                            │
    │    venue, teams,            batter, bowler,                      │
    │    winner, date)            runs, wickets)                       │
    │         │                        │                               │
    │         │                        ├──────────▶┌────────────────┐  │
    │         │                        │           │ batting_metrics│  │
    │         │                        │           └────────────────┘  │
    │         │                        │           (batter, runs,      │
    │         │                        │            avg, SR, 50s)      │
    │         │                        │                               │
    │         │                        ├──────────▶┌────────────────┐  │
    │         │                        │           │ bowling_metrics│  │
    │         │                        │           └────────────────┘  │
    │         │                        │           (bowler, wickets,   │
    │         │                        │            avg, economy)      │
    │         │                        │                               │
    │         │                        └──────────▶┌────────────────┐  │
    │         │                                    │  team_metrics  │  │
    │         │                                    └────────────────┘  │
    │         │                                    (team, wins, win%)  │
    │         │                                                        │
    │         └───────────────────────▶┌────────────────┐              │
    │                                  │ impact_players │              │
    │                                  └────────────────┘              │
    │                                  (match_id, player_in,           │
    │                                   player_out)                    │
    │                                                                  │
    │  ┌──────────┐                                                    │
    │  │  people  │◀─── JOIN on batter/bowler name for player photos   │
    │  └──────────┘                                                    │
    │  (name, key_cricinfo)                                            │
    │                                                                  │
    └───────────────────────────────────────────────────────────────────┘
    ```

    **Key Joins:**
    - `stg_deliveries.match_id` = `stg_matches.match_id`
    - `stg_deliveries.batter` = `people.name` (for player photos via key_cricinfo)
    - `batting_metrics.batter` = `bowling_metrics.bowler` (for all-rounders)
    - `impact_players.match_id` = `stg_matches.match_id`
    """)

# Table Explorer
with st.expander("🔎 Explore Tables", expanded=False):
    tables = [
        "batting_metrics", "bowling_metrics", "team_metrics",
        "stg_matches", "stg_deliveries", "people", "impact_players"
    ]

    selected_table = st.selectbox("Select Table", tables)

    if selected_table:
        # Show columns
        st.markdown(f"**Columns in `{selected_table}`:**")
        cols_df = run_query(f"DESCRIBE {selected_table}")
        cols_df = cols_df[['column_name', 'column_type', 'null']]
        st.dataframe(cols_df, use_container_width=True, hide_index=True)

        # Show sample data
        st.markdown(f"**Sample Data (5 rows):**")
        sample_df = run_query(f"SELECT * FROM {selected_table} LIMIT 5")
        st.dataframe(sample_df, use_container_width=True, hide_index=True)

st.divider()

st.markdown("""
**Available Tables:**

| Table | Description |
|-------|-------------|
| `batting_metrics` | Aggregated batting stats (runs, avg, SR, 50s, 100s) |
| `bowling_metrics` | Aggregated bowling stats (wickets, avg, economy, SR) |
| `team_metrics` | Team-level statistics (matches, wins, win %) |
| `stg_matches` | Match details (date, venue, teams, winner) |
| `stg_deliveries` | Ball-by-ball data (runs, wickets, extras) |
| `people` | Player registry (name, cricinfo_id for photos) |
| `impact_players` | Impact player substitutions (2023+) |
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
