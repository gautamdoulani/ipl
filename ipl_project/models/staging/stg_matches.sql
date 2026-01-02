{{ config(materialized='view') }}

select
    match_id,
    season,
    city,
    venue,
    match_date,
    match_number,
    event_name,
    match_type,
    overs,
    team1,
    team2,
    toss_winner,
    toss_decision,
    winner,
    win_by_runs,
    win_by_wickets,
    player_of_match
from {{ source('raw', 'matches') }}
