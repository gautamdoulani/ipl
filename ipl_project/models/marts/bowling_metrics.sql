{{ config(materialized='table') }}

with bowling_innings as (
    select
        d.match_id,
        d.season,
        d.bowler_id,
        d.bowler,
        d.bowler_cricinfo_id,
        sum(d.total_runs) as runs_conceded,
        count(*) as balls_bowled,
        sum(case
            when d.is_wicket and d.wicket_kind not in ('run out', 'retired hurt', 'retired out', 'obstructing the field')
            then 1 else 0
        end) as wickets,
        sum(case when d.total_runs = 0 then 1 else 0 end) as dot_balls,
        sum(case when d.batter_runs = 4 then 1 else 0 end) as fours_conceded,
        sum(case when d.batter_runs = 6 then 1 else 0 end) as sixes_conceded,
        sum(case when d.extras_type like '%wides%' or d.extras_type like '%noballs%' then 1 else 0 end) as extras_given
    from {{ ref('stg_deliveries') }} d
    group by d.match_id, d.season, d.bowler_id, d.bowler, d.bowler_cricinfo_id
),

bowling_aggregates as (
    select
        bowler_id,
        bowler,
        max(bowler_cricinfo_id) as cricinfo_id,
        count(distinct match_id) as matches,
        count(*) as innings,
        cast(sum(runs_conceded) as integer) as total_runs_conceded,
        cast(sum(balls_bowled) as integer) as total_balls,
        cast(sum(wickets) as integer) as total_wickets,
        cast(sum(dot_balls) as integer) as total_dot_balls,
        cast(sum(fours_conceded) as integer) as total_fours_conceded,
        cast(sum(sixes_conceded) as integer) as total_sixes_conceded,
        cast(sum(extras_given) as integer) as total_extras,
        cast(max(wickets) as integer) as best_wickets_innings
    from bowling_innings
    group by bowler_id, bowler
),

best_figures as (
    select
        bowler_id,
        wickets as best_wickets,
        runs_conceded as best_runs
    from bowling_innings
    qualify row_number() over (partition by bowler_id order by wickets desc, runs_conceded asc) = 1
)

select
    ba.bowler_id,
    ba.bowler,
    ba.cricinfo_id,
    ba.matches,
    ba.innings,
    ba.total_balls,
    cast(floor(ba.total_balls / 6) as integer) || '.' || (ba.total_balls % 6) as overs,
    ba.total_runs_conceded,
    ba.total_wickets,
    ba.total_dot_balls,
    ba.total_fours_conceded,
    ba.total_sixes_conceded,

    -- Best bowling figures
    bf.best_wickets || '/' || bf.best_runs as best_bowling,

    -- Bowling Average: runs conceded / wickets
    round(ba.total_runs_conceded * 1.0 / nullif(ba.total_wickets, 0), 2) as bowling_average,

    -- Economy Rate: runs conceded per over (runs * 6 / balls)
    round(ba.total_runs_conceded * 6.0 / nullif(ba.total_balls, 0), 2) as economy_rate,

    -- Strike Rate: balls per wicket
    round(ba.total_balls * 1.0 / nullif(ba.total_wickets, 0), 2) as strike_rate,

    -- Dot ball percentage
    round(ba.total_dot_balls * 100.0 / nullif(ba.total_balls, 0), 2) as dot_ball_percentage,

    -- 4+ wicket hauls
    (select count(*) from bowling_innings bi where bi.bowler_id = ba.bowler_id and bi.wickets >= 4) as four_wicket_hauls,

    -- 5+ wicket hauls
    (select count(*) from bowling_innings bi where bi.bowler_id = ba.bowler_id and bi.wickets >= 5) as five_wicket_hauls

from bowling_aggregates ba
left join best_figures bf on ba.bowler_id = bf.bowler_id
where ba.total_balls > 0
order by ba.total_wickets desc
