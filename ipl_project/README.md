# IPL Data Explorer

A Streamlit app for exploring Indian Premier League (IPL) cricket data from 2008-2025.

## Features

- **Overview** - Season summaries, top performers, and key statistics
- **Batting Stats** - Comprehensive batting leaderboards with filters
- **Bowling Stats** - Bowling performance analysis and rankings
- **Player Profile** - Deep dive into individual player careers
- **Match Analysis** - Detailed match scorecards and ball-by-ball breakdowns
- **Stadium Profile** - Venue statistics and records
- **Team vs Team** - Head-to-head team comparisons
- **Player vs Player** - Compare two players side by side
- **Player vs Team** - How a player performs against specific teams
- **Player at Venue** - Player performance at different stadiums
- **Impact Players** - Analysis of the IPL Impact Player rule
- **SQL Query** - Run custom SQL queries on the data

## Data

- **1,169 matches** from 2008 to 2025
- **278,205 ball-by-ball deliveries**
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

This is a fan-made application for educational and entertainment purposes. It is not affiliated with the IPL, BCCI, or any IPL franchise.
