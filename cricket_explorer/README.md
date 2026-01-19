# Cricket Data Explorer

A Streamlit-based analytics dashboard for exploring IPL (Indian Premier League) and WPL (Women's Premier League) cricket data.

## Features

- **Overview** - Trophy cabinet, season-wise champions, team performance matrix
- **Batting Stats** - Top run scorers, best strike rates, best averages
- **Bowling Stats** - Top wicket takers, best economy rates, wicket hauls
- **Player Profile** - Detailed career stats, most faced bowlers/batters
- **Compare Players** - Side-by-side comparison of two players
- **Match Analysis** - Ball-by-ball scorecards with batting/bowling details
- **Stadium Profile** - Venue statistics, chase vs defend records
- **Team vs Team** - Head-to-head records between teams
- **Player vs Player** - Batter vs bowler matchup statistics
- **Player vs Team** - How a player performs against specific teams
- **Player at Venue** - Player performance at different stadiums
- **Impact Players** - Analysis of impact player substitutions (IPL 2023+)
- **SQL Query** - Run custom SQL queries against the database

## Data Source

Ball-by-ball cricket data from [Cricsheet](https://cricsheet.org/).

## Tech Stack

- **[Streamlit](https://streamlit.io/)** - Web application framework
- **[DuckDB](https://duckdb.org/)** - In-process analytical database
- **[dbt](https://www.getdbt.com/)** - Data transformation and semantic layer
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation

## Project Structure

```
cricket_explorer/
├── ipl_app.py              # IPL app entry point
├── wpl_app.py              # WPL app entry point
├── config.py               # League configuration
├── utils.py                # Shared utilities
├── requirements.txt        # Python dependencies
├── pages/                  # Streamlit pages
│   ├── 0_Overview.py
│   ├── 1_Batting_Stats.py
│   ├── 2_Bowling_Stats.py
│   ├── 3_Match_Analysis.py
│   ├── 4_Team_vs_Team.py
│   ├── 5_Player_vs_Player.py
│   ├── 6_Player_vs_Team.py
│   ├── 7_Player_at_Venue.py
│   ├── 8_Impact_Players.py
│   ├── 9_SQL_Query.py
│   ├── 11_Player_Profile.py
│   ├── 12_Stadium_Profile.py
│   ├── 13_Credits.py
│   └── 14_Compare_Players.py
├── data/
│   ├── ipl.duckdb          # IPL database
│   └── wpl.duckdb          # WPL database
├── logos/                  # Team logos
└── .streamlit/
    └── config.toml         # Streamlit theme configuration
```

## Running Locally

### Prerequisites

- Python 3.9+
- pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd cricket_explorer

# Install dependencies
pip install -r requirements.txt
```

### Running the Apps

```bash
# Run IPL Data Explorer
streamlit run ipl_app.py --server.port 8501

# Run WPL Data Explorer
streamlit run wpl_app.py --server.port 8502
```

## Deployment

### Streamlit Cloud

1. Push the repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Deploy with:
   - **IPL**: Main file = `ipl_app.py`
   - **WPL**: Main file = `wpl_app.py`

## Database Schema

### Staging Tables
- `stg_matches` - Match details (date, venue, teams, winner)
- `stg_deliveries` - Ball-by-ball data (runs, wickets, extras)

### Semantic Layer (Metrics)
- `batting_metrics` - Aggregated batting stats per player
- `bowling_metrics` - Aggregated bowling stats per player
- `team_metrics` - Team-level statistics

### Other Tables
- `people` - Player registry with cricinfo IDs
- `impact_players` - Impact player substitutions (IPL 2023+)

## License

This is a fan-made application for educational purposes. Not affiliated with IPL, WPL, BCCI, or any franchise.
