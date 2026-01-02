"""IPL Data Explorer - Credits page."""

import streamlit as st


st.title("🙏 Credits")

st.markdown("""
## Data Source

This application uses ball-by-ball IPL cricket data from [Cricsheet](https://cricsheet.org/).

Cricsheet provides freely available structured data for cricket matches, making it possible to build detailed analytics applications like this one.

---

## Built With

- **[Streamlit](https://streamlit.io/)** - The web application framework
- **[DuckDB](https://duckdb.org/)** - In-process analytical database
- **[dbt](https://www.getdbt.com/)** - Data transformation and semantic layer
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation and analysis

---

## Player Photos

Player photos are sourced from ESPN Cricinfo via their public headshots API.

---

## Team Logos

Team logos are property of their respective IPL franchises and are used for identification purposes only.

---

## Disclaimer

This is a fan-made application for educational and entertainment purposes. It is not affiliated with, endorsed by, or connected to the Indian Premier League (IPL), BCCI, or any IPL franchise.

---

## Feedback

Found a bug or have a suggestion? We'd love to hear from you!

📧 [Send feedback via email](mailto:gautamoncloud9@gmail.com?subject=IPL%20Explorer%20Feedback)
""")
