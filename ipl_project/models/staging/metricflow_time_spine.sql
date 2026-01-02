{{ config(materialized='table') }}

with date_spine as (
    select
        unnest(generate_series(
            date '2008-01-01',
            date '2025-12-31',
            interval '1 day'
        ))::date as date_day
)

select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    extract(quarter from date_day) as quarter,
    extract(week from date_day) as week_of_year,
    extract(dayofweek from date_day) as day_of_week
from date_spine
