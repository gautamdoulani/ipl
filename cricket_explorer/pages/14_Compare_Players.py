"""Cricket Data Explorer - Compare two players' overall stats side by side."""

import streamlit as st
from utils import run_query, display_player_image


st.title("📊 Compare Players")
st.caption("Side-by-side comparison of two players' career stats")

# Get list of all players with significant appearances
players = run_query("""
    SELECT DISTINCT name FROM (
        SELECT batter as name FROM batting_metrics WHERE total_balls >= 100
        UNION
        SELECT bowler as name FROM bowling_metrics WHERE total_balls >= 100
    )
    ORDER BY name
""")

col1, col2 = st.columns(2)
with col1:
    player1 = st.selectbox("Select Player 1", players['name'].tolist(), key="p1")
with col2:
    player2 = st.selectbox("Select Player 2", players['name'].tolist(), index=1, key="p2")

if player1 and player2:
    # Get batting stats for both players
    batting_stats = run_query(f"""
        SELECT
            batter as name,
            total_runs,
            total_balls,
            total_innings,
            total_dismissals,
            total_fours,
            total_sixes,
            fifties,
            hundreds,
            ROUND(total_runs * 100.0 / NULLIF(total_balls, 0), 2) as strike_rate,
            ROUND(total_runs * 1.0 / NULLIF(total_dismissals, 0), 2) as average,
            highest_score
        FROM batting_metrics
        WHERE batter IN ('{player1}', '{player2}')
    """)

    # Get bowling stats for both players
    bowling_stats = run_query(f"""
        SELECT
            bowler as name,
            total_wickets,
            total_balls as balls_bowled,
            total_runs_conceded,
            total_maidens,
            ROUND(total_runs_conceded * 6.0 / NULLIF(total_balls, 0), 2) as economy,
            ROUND(total_balls * 1.0 / NULLIF(total_wickets, 0), 2) as bowling_strike_rate,
            ROUND(total_runs_conceded * 1.0 / NULLIF(total_wickets, 0), 2) as bowling_average,
            best_bowling_wickets,
            best_bowling_runs,
            four_wicket_hauls,
            five_wicket_hauls
        FROM bowling_metrics
        WHERE bowler IN ('{player1}', '{player2}')
    """)

    # Get player images
    player_info = run_query(f"""
        SELECT name, key_cricinfo,
               'https://a.espncdn.com/i/headshots/cricket/players/full/' || key_cricinfo || '.png' as photo_url
        FROM people
        WHERE name IN ('{player1}', '{player2}')
    """)

    # Display player cards
    col1, col2 = st.columns(2)

    for idx, (col, player) in enumerate([(col1, player1), (col2, player2)]):
        with col:
            info = player_info[player_info['name'] == player]
            if len(info) > 0:
                display_player_image(info['photo_url'].iloc[0], info['key_cricinfo'].iloc[0], size=120)
            st.markdown(f"### {player}")

    st.divider()

    # Batting comparison
    st.subheader("Batting Stats")

    p1_batting = batting_stats[batting_stats['name'] == player1]
    p2_batting = batting_stats[batting_stats['name'] == player2]

    if len(p1_batting) > 0 or len(p2_batting) > 0:
        def get_bat_stat(df, col, default=0):
            if len(df) > 0 and col in df.columns:
                val = df[col].iloc[0]
                return val if val is not None else default
            return default

        batting_metrics = [
            ("Innings", "total_innings"),
            ("Runs", "total_runs"),
            ("Balls", "total_balls"),
            ("Average", "average"),
            ("Strike Rate", "strike_rate"),
            ("Highest Score", "highest_score"),
            ("50s", "fifties"),
            ("100s", "hundreds"),
            ("4s", "total_fours"),
            ("6s", "total_sixes"),
        ]

        col1, col2, col3 = st.columns([2, 1, 2])

        for label, key in batting_metrics:
            val1 = get_bat_stat(p1_batting, key, "-")
            val2 = get_bat_stat(p2_batting, key, "-")

            # Determine which is better (higher is better for batting)
            highlight1 = ""
            highlight2 = ""
            if val1 != "-" and val2 != "-":
                try:
                    if float(val1) > float(val2):
                        highlight1 = "**"
                    elif float(val2) > float(val1):
                        highlight2 = "**"
                except:
                    pass

            with col1:
                st.markdown(f"{highlight1}{val1}{highlight1}")
            with col2:
                st.markdown(f"**{label}**")
            with col3:
                st.markdown(f"{highlight2}{val2}{highlight2}")
    else:
        st.info("No batting stats available for these players")

    st.divider()

    # Bowling comparison
    st.subheader("Bowling Stats")

    p1_bowling = bowling_stats[bowling_stats['name'] == player1]
    p2_bowling = bowling_stats[bowling_stats['name'] == player2]

    if len(p1_bowling) > 0 or len(p2_bowling) > 0:
        def get_bowl_stat(df, col, default=0):
            if len(df) > 0 and col in df.columns:
                val = df[col].iloc[0]
                return val if val is not None else default
            return default

        def format_best_bowling(df):
            if len(df) > 0:
                w = df['best_bowling_wickets'].iloc[0]
                r = df['best_bowling_runs'].iloc[0]
                if w is not None and r is not None:
                    return f"{int(w)}/{int(r)}"
            return "-"

        bowling_metrics = [
            ("Wickets", "total_wickets", False),
            ("Balls Bowled", "balls_bowled", False),
            ("Runs Conceded", "total_runs_conceded", True),
            ("Economy", "economy", True),
            ("Bowling Avg", "bowling_average", True),
            ("Bowling SR", "bowling_strike_rate", True),
            ("Maidens", "total_maidens", False),
            ("4W Hauls", "four_wicket_hauls", False),
            ("5W Hauls", "five_wicket_hauls", False),
        ]

        col1, col2, col3 = st.columns([2, 1, 2])

        for label, key, lower_is_better in bowling_metrics:
            val1 = get_bowl_stat(p1_bowling, key, "-")
            val2 = get_bowl_stat(p2_bowling, key, "-")

            highlight1 = ""
            highlight2 = ""
            if val1 != "-" and val2 != "-" and val1 != 0 and val2 != 0:
                try:
                    v1, v2 = float(val1), float(val2)
                    if lower_is_better:
                        if v1 < v2:
                            highlight1 = "**"
                        elif v2 < v1:
                            highlight2 = "**"
                    else:
                        if v1 > v2:
                            highlight1 = "**"
                        elif v2 > v1:
                            highlight2 = "**"
                except:
                    pass

            with col1:
                st.markdown(f"{highlight1}{val1}{highlight1}")
            with col2:
                st.markdown(f"**{label}**")
            with col3:
                st.markdown(f"{highlight2}{val2}{highlight2}")

        # Best bowling
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            st.markdown(format_best_bowling(p1_bowling))
        with col2:
            st.markdown("**Best Bowling**")
        with col3:
            st.markdown(format_best_bowling(p2_bowling))
    else:
        st.info("No bowling stats available for these players")

    st.divider()

    # Head to head (if they've faced each other)
    st.subheader("Head to Head")

    h2h = run_query(f"""
        SELECT
            batter, bowler,
            COUNT(*) as balls,
            SUM(batter_runs) as runs,
            SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END) as dismissals
        FROM stg_deliveries
        WHERE (batter = '{player1}' AND bowler = '{player2}')
           OR (batter = '{player2}' AND bowler = '{player1}')
        GROUP BY batter, bowler
    """)

    if len(h2h) > 0:
        for _, row in h2h.iterrows():
            batter = row['batter']
            bowler = row['bowler']
            balls = int(row['balls'])
            runs = int(row['runs'])
            dismissals = int(row['dismissals'])
            sr = round(runs * 100 / balls, 1) if balls > 0 else 0

            st.markdown(f"**{batter}** vs {bowler}: {runs} runs off {balls} balls (SR: {sr}), dismissed {dismissals} time(s)")
    else:
        st.info("These players have not faced each other as batter vs bowler")
