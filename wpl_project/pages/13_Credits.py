"""WPL Data Explorer - Credits page."""

import streamlit as st

st.title("🙏 Credits")
st.caption("Acknowledgements and data sources")

st.markdown("""
## Data Source

All match data is sourced from [Cricsheet](https://cricsheet.org/), a fantastic open-source
repository of ball-by-ball cricket data.

- **Website:** [cricsheet.org](https://cricsheet.org/)
- **WPL Data:** [WPL JSON Downloads](https://cricsheet.org/downloads/wpl_json.zip)
- **License:** The data is made available under the [Open Data Commons Attribution License](https://opendatacommons.org/licenses/by/1.0/)

## Technology Stack

This application is built with:

- **[Streamlit](https://streamlit.io/)** - The web application framework
- **[DuckDB](https://duckdb.org/)** - In-process analytical database
- **[Pandas](https://pandas.pydata.org/)** - Data manipulation and analysis

## About WPL

The Women's Premier League (WPL) is a professional Twenty20 cricket league in India,
established by the Board of Control for Cricket in India (BCCI) in 2023.

**Teams:**
- Delhi Capitals
- Gujarat Giants
- Mumbai Indians
- Royal Challengers Bengaluru
- UP Warriorz

## Disclaimer

This is a fan-made application for educational and entertainment purposes.
It is not affiliated with the WPL, BCCI, or any WPL franchise.

---

Made with ❤️ for cricket fans
""")
