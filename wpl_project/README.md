# WPL Data Explorer

A Streamlit app for exploring Women's Premier League (WPL) cricket data from 2023-2025.

## Features

- **Overview** - Season summaries, top performers, and key statistics
- **Batting Stats** - Comprehensive batting leaderboards with filters
- **Bowling Stats** - Bowling performance analysis and rankings
- **Player Profile** - Deep dive into individual player careers
- **Match Analysis** - Detailed match scorecards and ball-by-ball breakdowns
- **Stadium Profile** - Venue statistics and records
- **Team vs Team** - Head-to-head team comparisons
- **Player vs Player** - Batter vs Bowler matchups
- **Player vs Team** - How a player performs against specific teams
- **Compare Players** - Side-by-side career comparison
- **SQL Query** - Run custom SQL queries on the data

## Data

- **66 matches** from 2023 to 2025 (3 seasons)
- **15,406 ball-by-ball deliveries**
- **5 teams**: Delhi Capitals, Gujarat Giants, Mumbai Indians, Royal Challengers Bengaluru, UP Warriorz
- Source: [Cricsheet](https://cricsheet.org/)

## Tech Stack

- **[Streamlit](https://streamlit.io/)** - Web application framework
- **[DuckDB](https://duckdb.org/)** - In-process analytical database
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation

## Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Deployment

This app is ready for deployment on [Streamlit Cloud](https://streamlit.io/cloud).

## License

This is a fan-made application for educational and entertainment purposes. It is not affiliated with the WPL, BCCI, or any WPL franchise.
