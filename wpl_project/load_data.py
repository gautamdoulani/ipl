#!/usr/bin/env python3
"""Load WPL JSON data into DuckDB."""

import json
import duckdb
from pathlib import Path

def load_wpl_data():
    # Connect to DuckDB
    db_path = Path(__file__).parent / "wpl.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create tables with player IDs from registry
    conn.execute("""
        CREATE OR REPLACE TABLE matches (
            match_id VARCHAR PRIMARY KEY,
            season VARCHAR,
            city VARCHAR,
            venue VARCHAR,
            match_date DATE,
            match_number INTEGER,
            event_name VARCHAR,
            match_type VARCHAR,
            gender VARCHAR,
            overs INTEGER,
            balls_per_over INTEGER,
            team1 VARCHAR,
            team2 VARCHAR,
            toss_winner VARCHAR,
            toss_decision VARCHAR,
            winner VARCHAR,
            win_by_runs INTEGER,
            win_by_wickets INTEGER,
            player_of_match VARCHAR,
            player_of_match_id VARCHAR,
            umpire1 VARCHAR,
            umpire2 VARCHAR
        )
    """)

    conn.execute("""
        CREATE OR REPLACE TABLE deliveries (
            match_id VARCHAR,
            innings INTEGER,
            batting_team VARCHAR,
            over_number INTEGER,
            ball_number INTEGER,
            batter VARCHAR,
            batter_id VARCHAR,
            bowler VARCHAR,
            bowler_id VARCHAR,
            non_striker VARCHAR,
            non_striker_id VARCHAR,
            batter_runs INTEGER,
            extras_runs INTEGER,
            total_runs INTEGER,
            extras_type VARCHAR,
            is_wicket BOOLEAN,
            wicket_kind VARCHAR,
            wicket_player_out VARCHAR,
            wicket_player_out_id VARCHAR,
            wicket_fielders VARCHAR
        )
    """)

    conn.execute("""
        CREATE OR REPLACE TABLE impact_players (
            match_id VARCHAR,
            season VARCHAR,
            team VARCHAR,
            player_in VARCHAR,
            player_in_id VARCHAR,
            player_out VARCHAR,
            player_out_id VARCHAR
        )
    """)

    # Load JSON files
    json_dir = Path(__file__).parent / "wpl_json"
    json_files = list(json_dir.glob("*.json"))

    matches_data = []
    deliveries_data = []
    impact_players_data = []

    print(f"Processing {len(json_files)} JSON files...")

    for i, json_file in enumerate(json_files):
        if json_file.name == "README.txt":
            continue

        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except:
            continue

        match_id = json_file.stem
        info = data.get('info', {})

        # Get registry for player ID lookups
        registry = info.get('registry', {}).get('people', {})

        # Extract match info
        dates = info.get('dates', [])
        match_date = dates[0] if dates else None

        teams = info.get('teams', [])
        team1 = teams[0] if len(teams) > 0 else None
        team2 = teams[1] if len(teams) > 1 else None

        toss = info.get('toss', {})
        outcome = info.get('outcome', {})

        # Winner info
        winner = outcome.get('winner')
        win_by = outcome.get('by', {})
        win_by_runs = win_by.get('runs')
        win_by_wickets = win_by.get('wickets')

        # Player of match
        pom = info.get('player_of_match', [])
        player_of_match = pom[0] if pom else None
        player_of_match_id = registry.get(player_of_match) if player_of_match else None

        # Umpires
        officials = info.get('officials', {})
        umpires = officials.get('umpires', [])
        umpire1 = umpires[0] if len(umpires) > 0 else None
        umpire2 = umpires[1] if len(umpires) > 1 else None

        # Event info
        event = info.get('event', {})

        # Season from dates
        season = match_date[:4] if match_date else None

        matches_data.append({
            'match_id': match_id,
            'season': season,
            'city': info.get('city'),
            'venue': info.get('venue'),
            'match_date': match_date,
            'match_number': event.get('match_number'),
            'event_name': event.get('name'),
            'match_type': info.get('match_type'),
            'gender': info.get('gender'),
            'overs': info.get('overs'),
            'balls_per_over': info.get('balls_per_over'),
            'team1': team1,
            'team2': team2,
            'toss_winner': toss.get('winner'),
            'toss_decision': toss.get('decision'),
            'winner': winner,
            'win_by_runs': win_by_runs,
            'win_by_wickets': win_by_wickets,
            'player_of_match': player_of_match,
            'player_of_match_id': player_of_match_id,
            'umpire1': umpire1,
            'umpire2': umpire2
        })

        # Extract deliveries with player IDs
        for innings_num, innings in enumerate(data.get('innings', []), 1):
            batting_team = innings.get('team')

            for over_data in innings.get('overs', []):
                over_number = over_data.get('over')

                for ball_num, delivery in enumerate(over_data.get('deliveries', []), 1):
                    runs = delivery.get('runs', {})
                    extras = delivery.get('extras', {})

                    # Determine extras type
                    extras_type = None
                    if extras:
                        extras_type = ','.join(extras.keys())

                    # Player names and IDs
                    batter = delivery.get('batter')
                    bowler = delivery.get('bowler')
                    non_striker = delivery.get('non_striker')

                    batter_id = registry.get(batter)
                    bowler_id = registry.get(bowler)
                    non_striker_id = registry.get(non_striker)

                    # Wicket info
                    wickets = delivery.get('wickets', [])
                    is_wicket = len(wickets) > 0
                    wicket_kind = None
                    wicket_player_out = None
                    wicket_player_out_id = None
                    wicket_fielders = None

                    if wickets:
                        w = wickets[0]
                        wicket_kind = w.get('kind')
                        wicket_player_out = w.get('player_out')
                        wicket_player_out_id = registry.get(wicket_player_out)
                        fielders = w.get('fielders', [])
                        if fielders:
                            wicket_fielders = ','.join([f.get('name', str(f)) if isinstance(f, dict) else str(f) for f in fielders])

                    deliveries_data.append({
                        'match_id': match_id,
                        'innings': innings_num,
                        'batting_team': batting_team,
                        'over_number': over_number,
                        'ball_number': ball_num,
                        'batter': batter,
                        'batter_id': batter_id,
                        'bowler': bowler,
                        'bowler_id': bowler_id,
                        'non_striker': non_striker,
                        'non_striker_id': non_striker_id,
                        'batter_runs': runs.get('batter', 0),
                        'extras_runs': runs.get('extras', 0),
                        'total_runs': runs.get('total', 0),
                        'extras_type': extras_type,
                        'is_wicket': is_wicket,
                        'wicket_kind': wicket_kind,
                        'wicket_player_out': wicket_player_out,
                        'wicket_player_out_id': wicket_player_out_id,
                        'wicket_fielders': wicket_fielders
                    })

                    # Extract impact player replacements
                    replacements = delivery.get('replacements', {})
                    match_replacements = replacements.get('match', [])
                    for repl in match_replacements:
                        if repl.get('reason') == 'impact_player':
                            player_in = repl.get('in')
                            player_out = repl.get('out')
                            team = repl.get('team')
                            impact_players_data.append({
                                'match_id': match_id,
                                'season': season,
                                'team': team,
                                'player_in': player_in,
                                'player_in_id': registry.get(player_in),
                                'player_out': player_out,
                                'player_out_id': registry.get(player_out)
                            })

        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1} files...")

    # Insert data
    print(f"\nInserting {len(matches_data)} matches...")
    conn.executemany("""
        INSERT INTO matches VALUES (
            $match_id, $season, $city, $venue, $match_date, $match_number,
            $event_name, $match_type, $gender, $overs, $balls_per_over,
            $team1, $team2, $toss_winner, $toss_decision, $winner,
            $win_by_runs, $win_by_wickets, $player_of_match, $player_of_match_id,
            $umpire1, $umpire2
        )
    """, matches_data)

    print(f"Inserting {len(deliveries_data)} deliveries...")
    conn.executemany("""
        INSERT INTO deliveries VALUES (
            $match_id, $innings, $batting_team, $over_number, $ball_number,
            $batter, $batter_id, $bowler, $bowler_id, $non_striker, $non_striker_id,
            $batter_runs, $extras_runs, $total_runs, $extras_type, $is_wicket,
            $wicket_kind, $wicket_player_out, $wicket_player_out_id, $wicket_fielders
        )
    """, deliveries_data)

    if impact_players_data:
        print(f"Inserting {len(impact_players_data)} impact player records...")
        conn.executemany("""
            INSERT INTO impact_players VALUES (
                $match_id, $season, $team, $player_in, $player_in_id, $player_out, $player_out_id
            )
        """, impact_players_data)

    conn.commit()

    # Create views to match IPL structure exactly
    print("\nCreating views and tables to match IPL structure...")

    # People table (extract from registry)
    conn.execute("""
        CREATE OR REPLACE TABLE people AS
        SELECT DISTINCT
            batter as name,
            batter_id as key_cricinfo
        FROM deliveries
        WHERE batter_id IS NOT NULL
        UNION
        SELECT DISTINCT
            bowler as name,
            bowler_id as key_cricinfo
        FROM deliveries
        WHERE bowler_id IS NOT NULL
    """)

    # stg_matches view (matches with normalized data)
    conn.execute("""
        CREATE OR REPLACE VIEW stg_matches AS
        SELECT
            match_id,
            season,
            city,
            venue,
            match_date,
            match_number,
            event_name,
            match_type,
            gender,
            overs,
            balls_per_over,
            team1,
            team2,
            toss_winner,
            toss_decision,
            winner,
            win_by_runs,
            win_by_wickets,
            player_of_match,
            player_of_match_id
        FROM matches
    """)

    # stg_deliveries view with cricinfo IDs (to match IPL structure)
    conn.execute("""
        CREATE OR REPLACE VIEW stg_deliveries AS
        SELECT
            d.match_id,
            d.innings,
            d.batting_team,
            d.over_number,
            d.ball_number,
            d.batter,
            d.batter_id as batter_cricinfo_id,
            d.bowler,
            d.bowler_id as bowler_cricinfo_id,
            d.non_striker,
            d.non_striker_id as non_striker_cricinfo_id,
            d.batter_runs,
            d.extras_runs,
            d.total_runs,
            d.extras_type,
            d.is_wicket,
            d.wicket_kind,
            d.wicket_player_out,
            d.wicket_player_out_id as wicket_player_out_cricinfo_id,
            d.wicket_fielders,
            m.season,
            m.venue,
            m.city,
            m.match_date,
            m.winner as match_winner,
            m.player_of_match
        FROM deliveries d
        JOIN matches m ON d.match_id = m.match_id
    """)

    # team_metrics view
    conn.execute("""
        CREATE OR REPLACE VIEW team_metrics AS
        WITH team_matches AS (
            SELECT team, match_id, winner
            FROM (
                SELECT team1 as team, match_id, winner FROM matches
                UNION ALL
                SELECT team2 as team, match_id, winner FROM matches
            )
        ),
        team_batting AS (
            SELECT
                batting_team as team,
                SUM(total_runs) as total_runs,
                COUNT(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 END) as balls
            FROM deliveries
            GROUP BY batting_team
        ),
        team_bowling AS (
            SELECT
                m.team1 as team,
                SUM(d.total_runs) as runs_conceded
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE d.batting_team = m.team2
            GROUP BY m.team1
            UNION ALL
            SELECT
                m.team2 as team,
                SUM(d.total_runs) as runs_conceded
            FROM deliveries d
            JOIN matches m ON d.match_id = m.match_id
            WHERE d.batting_team = m.team1
            GROUP BY m.team2
        )
        SELECT
            tm.team,
            COUNT(DISTINCT tm.match_id) as matches_played,
            SUM(CASE WHEN tm.team = tm.winner THEN 1 ELSE 0 END) as matches_won,
            ROUND(SUM(CASE WHEN tm.team = tm.winner THEN 1 ELSE 0 END) * 100.0 / COUNT(DISTINCT tm.match_id), 2) as win_percentage,
            ROUND(tb.total_runs * 100.0 / NULLIF(tb.balls, 0), 2) as team_strike_rate,
            ROUND(tbo.runs_conceded * 6.0 / NULLIF(tb.balls, 0), 2) as team_economy_rate
        FROM team_matches tm
        LEFT JOIN team_batting tb ON tm.team = tb.team
        LEFT JOIN (SELECT team, SUM(runs_conceded) as runs_conceded FROM team_bowling GROUP BY team) tbo ON tm.team = tbo.team
        GROUP BY tm.team, tb.total_runs, tb.balls, tbo.runs_conceded
    """)

    # batting_metrics view (matching IPL structure with cricinfo_id)
    conn.execute("""
        CREATE OR REPLACE VIEW batting_metrics AS
        WITH batting_agg AS (
            SELECT
                batter,
                MAX(batter_id) as cricinfo_id,
                COUNT(DISTINCT match_id) as matches,
                COUNT(DISTINCT match_id || '-' || innings) as total_innings,
                SUM(batter_runs) as total_runs,
                SUM(CASE WHEN extras_type IS NULL OR extras_type NOT LIKE '%wides%' THEN 1 ELSE 0 END) as total_balls,
                SUM(CASE WHEN is_wicket AND wicket_player_out = batter THEN 1 ELSE 0 END) as total_dismissals,
                SUM(CASE WHEN batter_runs = 4 THEN 1 ELSE 0 END) as total_fours,
                SUM(CASE WHEN batter_runs = 6 THEN 1 ELSE 0 END) as total_sixes
            FROM deliveries
            GROUP BY batter
        ),
        innings_scores AS (
            SELECT
                batter,
                match_id,
                innings,
                SUM(batter_runs) as innings_runs
            FROM deliveries
            GROUP BY batter, match_id, innings
        ),
        milestones AS (
            SELECT
                batter,
                MAX(innings_runs) as highest_score,
                SUM(CASE WHEN innings_runs >= 50 AND innings_runs < 100 THEN 1 ELSE 0 END) as fifties,
                SUM(CASE WHEN innings_runs >= 100 THEN 1 ELSE 0 END) as hundreds
            FROM innings_scores
            GROUP BY batter
        )
        SELECT
            b.batter,
            b.cricinfo_id,
            b.matches,
            b.total_innings,
            b.total_runs,
            b.total_balls,
            b.total_dismissals,
            b.total_fours,
            b.total_sixes,
            ROUND(b.total_runs * 1.0 / NULLIF(b.total_dismissals, 0), 2) as batting_average,
            ROUND(b.total_runs * 100.0 / NULLIF(b.total_balls, 0), 2) as strike_rate,
            m.highest_score,
            m.fifties,
            m.hundreds
        FROM batting_agg b
        LEFT JOIN milestones m ON b.batter = m.batter
    """)

    # bowling_metrics view (matching IPL structure with cricinfo_id)
    conn.execute("""
        CREATE OR REPLACE VIEW bowling_metrics AS
        WITH bowling_innings AS (
            SELECT
                bowler,
                match_id,
                innings,
                SUM(total_runs) - SUM(CASE WHEN extras_type LIKE '%legbyes%' OR extras_type LIKE '%byes%' THEN extras_runs ELSE 0 END) as runs_conceded,
                SUM(CASE WHEN extras_type IS NULL OR (extras_type NOT LIKE '%wides%' AND extras_type NOT LIKE '%noballs%') THEN 1 ELSE 0 END) as balls,
                SUM(CASE WHEN is_wicket AND wicket_kind NOT IN ('run out', 'retired hurt', 'retired out', 'obstructing the field') THEN 1 ELSE 0 END) as wickets
            FROM deliveries
            GROUP BY bowler, match_id, innings
        ),
        best_figures AS (
            SELECT
                bowler,
                wickets as best_wickets,
                runs_conceded as best_runs,
                ROW_NUMBER() OVER (PARTITION BY bowler ORDER BY wickets DESC, runs_conceded ASC) as rn
            FROM bowling_innings
        ),
        bowling_agg AS (
            SELECT
                bi.bowler,
                MAX(d.bowler_id) as cricinfo_id,
                COUNT(DISTINCT bi.match_id) as matches,
                COUNT(*) as innings,
                SUM(runs_conceded) as total_runs_conceded,
                SUM(balls) as total_balls,
                SUM(wickets) as total_wickets,
                SUM(CASE WHEN wickets = 4 THEN 1 ELSE 0 END) as four_wickets,
                SUM(CASE WHEN wickets >= 5 THEN 1 ELSE 0 END) as five_wickets
            FROM bowling_innings bi
            JOIN (SELECT DISTINCT bowler, bowler_id FROM deliveries) d ON bi.bowler = d.bowler
            GROUP BY bi.bowler
        )
        SELECT
            ba.bowler,
            ba.cricinfo_id,
            ba.matches,
            ba.innings,
            ba.total_balls,
            ba.total_runs_conceded,
            ba.total_wickets,
            ROUND(ba.total_runs_conceded * 1.0 / NULLIF(ba.total_wickets, 0), 2) as bowling_average,
            ROUND(ba.total_runs_conceded * 6.0 / NULLIF(ba.total_balls, 0), 2) as economy_rate,
            ROUND(ba.total_balls * 1.0 / NULLIF(ba.total_wickets, 0), 2) as bowling_strike_rate,
            bf.best_wickets as best_bowling_wickets,
            bf.best_runs as best_bowling_runs,
            ba.four_wickets as four_wicket_hauls,
            ba.five_wickets as five_wicket_hauls
        FROM bowling_agg ba
        LEFT JOIN best_figures bf ON ba.bowler = bf.bowler AND bf.rn = 1
    """)

    # Verify
    print("\n--- Data loaded successfully ---")
    result = conn.execute("SELECT COUNT(*) as cnt FROM matches").fetchone()
    print(f"Matches: {result[0]}")

    result = conn.execute("SELECT COUNT(*) as cnt FROM deliveries").fetchone()
    print(f"Deliveries: {result[0]}")

    result = conn.execute("SELECT COUNT(DISTINCT batter_id) as cnt FROM deliveries WHERE batter_id IS NOT NULL").fetchone()
    print(f"Unique batters with ID: {result[0]}")

    result = conn.execute("SELECT COUNT(DISTINCT bowler_id) as cnt FROM deliveries WHERE bowler_id IS NOT NULL").fetchone()
    print(f"Unique bowlers with ID: {result[0]}")

    result = conn.execute("SELECT MIN(match_date), MAX(match_date) FROM matches").fetchone()
    print(f"Date range: {result[0]} to {result[1]}")

    result = conn.execute("SELECT DISTINCT season FROM matches ORDER BY season").fetchall()
    print(f"Seasons: {[r[0] for r in result]}")

    result = conn.execute("SELECT DISTINCT team1 FROM matches UNION SELECT DISTINCT team2 FROM matches").fetchall()
    print(f"Teams: {[r[0] for r in result]}")

    result = conn.execute("SELECT COUNT(*) as cnt FROM impact_players").fetchone()
    print(f"Impact player substitutions: {result[0]}")

    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    load_wpl_data()
