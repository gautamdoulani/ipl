{{ config(materialized='view') }}

-- Player IDs are now loaded directly from cricsheet registry (no ambiguity)
select
    d.match_id,
    m.match_date,
    m.season,
    d.innings,
    d.batting_team,
    d.over_number,
    d.ball_number,
    d.batter,
    d.batter_id,
    d.bowler,
    d.bowler_id,
    d.non_striker,
    d.non_striker_id,
    d.batter_runs,
    d.extras_runs,
    d.total_runs,
    d.extras_type,
    d.is_wicket,
    d.wicket_kind,
    d.wicket_player_out,
    d.wicket_player_out_id,
    d.wicket_fielders,
    -- Join to people table for cricinfo IDs (for photos)
    pb.key_cricinfo as batter_cricinfo_id,
    pw.key_cricinfo as bowler_cricinfo_id
from {{ source('raw', 'deliveries') }} d
left join {{ source('raw', 'matches') }} m on d.match_id = m.match_id
left join {{ source('raw', 'people') }} pb on d.batter_id = pb.identifier
left join {{ source('raw', 'people') }} pw on d.bowler_id = pw.identifier
