{{ config(materialized='table') }}

with batting_innings as (
    select
        d.match_id,
        d.season,
        d.batter_id,
        d.batter,
        d.batter_cricinfo_id,
        d.batting_team,
        sum(d.batter_runs) as runs,
        count(case when d.extras_type is null or d.extras_type not like '%wides%' then 1 end) as balls_faced,
        sum(case when d.batter_runs = 4 then 1 else 0 end) as fours,
        sum(case when d.batter_runs = 6 then 1 else 0 end) as sixes,
        max(case when d.is_wicket and d.wicket_player_out = d.batter then 1 else 0 end) as is_out
    from {{ ref('stg_deliveries') }} d
    group by d.match_id, d.season, d.batter_id, d.batter, d.batter_cricinfo_id, d.batting_team
),

batting_aggregates as (
    select
        batter_id,
        batter,
        max(batter_cricinfo_id) as cricinfo_id,
        count(distinct match_id) as matches,
        count(*) as innings,
        cast(sum(runs) as integer) as total_runs,
        cast(sum(balls_faced) as integer) as total_balls,
        cast(sum(fours) as integer) as total_fours,
        cast(sum(sixes) as integer) as total_sixes,
        cast(sum(is_out) as integer) as dismissals,
        cast(max(runs) as integer) as highest_score,
        cast(sum(case when runs >= 50 and runs < 100 then 1 else 0 end) as integer) as fifties,
        cast(sum(case when runs >= 100 then 1 else 0 end) as integer) as centuries
    from batting_innings
    group by batter_id, batter
)

select
    batter_id,
    batter,
    cricinfo_id,
    matches,
    innings,
    total_runs,
    total_balls,
    dismissals,
    highest_score,
    total_fours,
    total_sixes,
    fifties,
    centuries,

    -- Batting Average: runs / dismissals
    round(total_runs * 1.0 / nullif(dismissals, 0), 2) as batting_average,

    -- Strike Rate: (runs / balls) * 100
    round(total_runs * 100.0 / nullif(total_balls, 0), 2) as strike_rate,

    -- Boundary percentage
    round((total_fours * 4 + total_sixes * 6) * 100.0 / nullif(total_runs, 0), 2) as boundary_percentage

from batting_aggregates
where total_balls > 0
order by total_runs desc
