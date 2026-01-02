{{ config(materialized='table') }}

with team_matches as (
    select
        team1 as team,
        season,
        match_id,
        case when winner = team1 then 1 else 0 end as won,
        case when winner is null then 1 else 0 end as no_result
    from {{ ref('stg_matches') }}

    union all

    select
        team2 as team,
        season,
        match_id,
        case when winner = team2 then 1 else 0 end as won,
        case when winner is null then 1 else 0 end as no_result
    from {{ ref('stg_matches') }}
),

team_batting as (
    select
        d.batting_team as team,
        m.match_id,
        sum(d.total_runs) as runs_scored,
        count(*) as balls_faced,
        sum(case when d.batter_runs = 4 then 1 else 0 end) as fours,
        sum(case when d.batter_runs = 6 then 1 else 0 end) as sixes
    from {{ ref('stg_deliveries') }} d
    join {{ ref('stg_matches') }} m on d.match_id = m.match_id
    group by d.batting_team, m.match_id
),

team_bowling as (
    select
        case
            when d.batting_team = m.team1 then m.team2
            else m.team1
        end as team,
        m.match_id,
        sum(d.total_runs) as runs_conceded,
        count(*) as balls_bowled,
        sum(case
            when d.is_wicket and d.wicket_kind not in ('run out', 'retired hurt', 'retired out', 'obstructing the field')
            then 1 else 0
        end) as wickets_taken
    from {{ ref('stg_deliveries') }} d
    join {{ ref('stg_matches') }} m on d.match_id = m.match_id
    group by
        case when d.batting_team = m.team1 then m.team2 else m.team1 end,
        m.match_id
)

select
    tm.team,
    count(distinct tm.match_id) as matches_played,
    sum(tm.won) as matches_won,
    count(distinct tm.match_id) - sum(tm.won) - sum(tm.no_result) as matches_lost,
    sum(tm.no_result) as no_results,

    -- Win percentage
    round(sum(tm.won) * 100.0 / nullif(count(distinct tm.match_id) - sum(tm.no_result), 0), 2) as win_percentage,

    -- Total runs scored
    sum(tb.runs_scored) as total_runs_scored,

    -- Average runs per match
    round(sum(tb.runs_scored) * 1.0 / nullif(count(distinct tm.match_id), 0), 2) as avg_runs_per_match,

    -- Total fours and sixes
    sum(tb.fours) as total_fours,
    sum(tb.sixes) as total_sixes,

    -- Batting strike rate
    round(sum(tb.runs_scored) * 100.0 / nullif(sum(tb.balls_faced), 0), 2) as team_strike_rate,

    -- Bowling metrics
    sum(tbo.wickets_taken) as total_wickets_taken,
    sum(tbo.runs_conceded) as total_runs_conceded,

    -- Bowling economy
    round(sum(tbo.runs_conceded) * 6.0 / nullif(sum(tbo.balls_bowled), 0), 2) as team_economy_rate,

    -- Net run rate components
    round(sum(tb.runs_scored) * 6.0 / nullif(sum(tb.balls_faced), 0), 2) as scoring_rate,
    round(sum(tbo.runs_conceded) * 6.0 / nullif(sum(tbo.balls_bowled), 0), 2) as conceding_rate

from team_matches tm
left join team_batting tb on tm.team = tb.team and tm.match_id = tb.match_id
left join team_bowling tbo on tm.team = tbo.team and tm.match_id = tbo.match_id
group by tm.team
order by matches_won desc
