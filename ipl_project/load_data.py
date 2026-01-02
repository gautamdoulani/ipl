#!/usr/bin/env python3
"""Load IPL JSON data into DuckDB."""

import json
import duckdb
from pathlib import Path

def load_ipl_data():
    # Connect to DuckDB
    db_path = Path(__file__).parent / "ipl.duckdb"
    conn = duckdb.connect(str(db_path))

    # Create tables
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
            bowler VARCHAR,
            non_striker VARCHAR,
            batter_runs INTEGER,
            extras_runs INTEGER,
            total_runs INTEGER,
            extras_type VARCHAR,
            is_wicket BOOLEAN,
            wicket_kind VARCHAR,
            wicket_player_out VARCHAR,
            wicket_fielders VARCHAR
        )
    """)

    # Load JSON files
    json_dir = Path(__file__).parent / "ipl_json"
    json_files = list(json_dir.glob("*.json"))

    matches_data = []
    deliveries_data = []

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
            'umpire1': umpire1,
            'umpire2': umpire2
        })

        # Extract deliveries
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

                    # Wicket info
                    wickets = delivery.get('wickets', [])
                    is_wicket = len(wickets) > 0
                    wicket_kind = None
                    wicket_player_out = None
                    wicket_fielders = None

                    if wickets:
                        w = wickets[0]
                        wicket_kind = w.get('kind')
                        wicket_player_out = w.get('player_out')
                        fielders = w.get('fielders', [])
                        if fielders:
                            wicket_fielders = ','.join([f.get('name', str(f)) if isinstance(f, dict) else str(f) for f in fielders])

                    deliveries_data.append({
                        'match_id': match_id,
                        'innings': innings_num,
                        'batting_team': batting_team,
                        'over_number': over_number,
                        'ball_number': ball_num,
                        'batter': delivery.get('batter'),
                        'bowler': delivery.get('bowler'),
                        'non_striker': delivery.get('non_striker'),
                        'batter_runs': runs.get('batter', 0),
                        'extras_runs': runs.get('extras', 0),
                        'total_runs': runs.get('total', 0),
                        'extras_type': extras_type,
                        'is_wicket': is_wicket,
                        'wicket_kind': wicket_kind,
                        'wicket_player_out': wicket_player_out,
                        'wicket_fielders': wicket_fielders
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
            $win_by_runs, $win_by_wickets, $player_of_match, $umpire1, $umpire2
        )
    """, matches_data)

    print(f"Inserting {len(deliveries_data)} deliveries...")
    conn.executemany("""
        INSERT INTO deliveries VALUES (
            $match_id, $innings, $batting_team, $over_number, $ball_number,
            $batter, $bowler, $non_striker, $batter_runs, $extras_runs,
            $total_runs, $extras_type, $is_wicket, $wicket_kind,
            $wicket_player_out, $wicket_fielders
        )
    """, deliveries_data)

    conn.commit()

    # Verify
    print("\n--- Data loaded successfully ---")
    result = conn.execute("SELECT COUNT(*) as cnt FROM matches").fetchone()
    print(f"Matches: {result[0]}")

    result = conn.execute("SELECT COUNT(*) as cnt FROM deliveries").fetchone()
    print(f"Deliveries: {result[0]}")

    result = conn.execute("SELECT MIN(match_date), MAX(match_date) FROM matches").fetchone()
    print(f"Date range: {result[0]} to {result[1]}")

    result = conn.execute("SELECT DISTINCT season FROM matches ORDER BY season").fetchall()
    print(f"Seasons: {', '.join([r[0] for r in result if r[0]])}")

    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    load_ipl_data()
