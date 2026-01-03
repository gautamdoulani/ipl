"""League configuration for Cricket Data Explorer."""

# Default league - will be overridden by app entry point
LEAGUE = "ipl"

# League-specific configurations
LEAGUE_CONFIG = {
    "ipl": {
        "name": "IPL",
        "display_name": "IPL Data Explorer",
        "db_file": "ipl.duckdb",
        "has_impact_players": True,
        "teams": {
            'Chennai Super Kings': '#FFCB05',
            'Mumbai Indians': '#004BA0',
            'Royal Challengers Bengaluru': '#EC1C24',
            'Royal Challengers Bangalore': '#EC1C24',
            'Kolkata Knight Riders': '#3A225D',
            'Delhi Capitals': '#004C93',
            'Delhi Daredevils': '#004C93',
            'Punjab Kings': '#DD1F2D',
            'Kings XI Punjab': '#DD1F2D',
            'Rajasthan Royals': '#EA1A85',
            'Sunrisers Hyderabad': '#F7A721',
            'Gujarat Titans': '#0B4973',
            'Lucknow Super Giants': '#00A9E0',
            'Deccan Chargers': '#D5A239',
            'Pune Warriors': '#2F9BE3',
            'Gujarat Lions': '#E04F16',
            'Rising Pune Supergiant': '#6F61A0',
            'Rising Pune Supergiants': '#6F61A0',
            'Kochi Tuskers Kerala': '#FF6B00',
        },
        "team_replacements": [
            ("Royal Challengers Bangalore", "Royal Challengers Bengaluru"),
            ("Rising Pune Supergiants", "Rising Pune Supergiant"),
            ("Kings XI Punjab", "Punjab Kings"),
            ("Delhi Daredevils", "Delhi Capitals"),
        ],
        "thresholds": {
            # Batting Stats page
            "batting_min_runs": (0, 2000, 100),  # (min, max, default)
            "batting_min_matches": (1, 100, 10),
            "batting_sr_min_runs": (50, 1000, 200),
            "batting_avg_min_runs": (50, 1000, 200),
            # Bowling Stats page
            "bowling_min_wickets": (0, 100, 10),
            "bowling_min_matches": (1, 100, 10),
            "bowling_econ_min_wickets": (5, 50, 20),
            "bowling_avg_min_wickets": (5, 50, 20),
            "bowling_sr_min_wickets": (5, 50, 20),
        },
    },
    "wpl": {
        "name": "WPL",
        "display_name": "WPL Data Explorer",
        "db_file": "wpl.duckdb",
        "has_impact_players": False,
        "teams": {
            'Mumbai Indians': '#004BA0',
            'Delhi Capitals': '#004C93',
            'Royal Challengers Bangalore': '#EC1C24',
            'Royal Challengers Bengaluru': '#EC1C24',
            'Gujarat Giants': '#E04F16',
            'UP Warriorz': '#6B3FA0',
        },
        "team_replacements": [
            ("Royal Challengers Bangalore", "Royal Challengers Bengaluru"),
        ],
        "thresholds": {
            # Batting Stats page - lower values for WPL (fewer seasons)
            "batting_min_runs": (0, 1000, 50),
            "batting_min_matches": (1, 50, 5),
            "batting_sr_min_runs": (50, 500, 100),
            "batting_avg_min_runs": (50, 500, 100),
            # Bowling Stats page
            "bowling_min_wickets": (0, 30, 5),
            "bowling_min_matches": (1, 30, 5),
            "bowling_econ_min_wickets": (5, 30, 10),
            "bowling_avg_min_wickets": (5, 30, 10),
            "bowling_sr_min_wickets": (5, 30, 10),
        },
    },
}

# Active configuration based on league
CONFIG = LEAGUE_CONFIG[LEAGUE]


def set_league(league: str):
    """Set the active league configuration. Must be called before importing other modules."""
    global LEAGUE, CONFIG
    LEAGUE = league.lower()
    CONFIG = LEAGUE_CONFIG[LEAGUE]


def get_threshold(name: str) -> tuple:
    """Get threshold tuple (min, max, default) for a given threshold name."""
    return CONFIG["thresholds"].get(name, (0, 100, 10))


def apply_team_replacements(text: str) -> str:
    """Apply league-specific team name replacements to text."""
    if text is None:
        return text
    for old_name, new_name in CONFIG["team_replacements"]:
        text = text.replace(old_name, new_name)
    return text


def get_team_replacement_sql(column: str) -> str:
    """Generate SQL REPLACE chain for team name normalization."""
    result = column
    for old_name, new_name in CONFIG["team_replacements"]:
        result = f"REPLACE({result}, '{old_name}', '{new_name}')"
    return result
