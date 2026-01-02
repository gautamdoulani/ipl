{{ config(materialized='view') }}

select
    match_id,
    season,
    city,
    venue as venue_original,
    -- Normalized venue names
    CASE
        -- Delhi
        WHEN venue LIKE '%Arun Jaitley%' OR venue LIKE '%Feroz Shah Kotla%' THEN 'Arun Jaitley Stadium, Delhi'
        -- Mumbai - Wankhede
        WHEN venue LIKE '%Wankhede%' THEN 'Wankhede Stadium, Mumbai'
        -- Mumbai - Brabourne
        WHEN venue LIKE '%Brabourne%' THEN 'Brabourne Stadium, Mumbai'
        -- Mumbai - DY Patil
        WHEN venue LIKE '%DY Patil%' OR venue LIKE '%Dr DY Patil%' THEN 'DY Patil Stadium, Mumbai'
        -- Kolkata
        WHEN venue LIKE '%Eden Gardens%' THEN 'Eden Gardens, Kolkata'
        -- Bengaluru
        WHEN venue LIKE '%Chinnaswamy%' THEN 'M Chinnaswamy Stadium, Bengaluru'
        -- Chennai
        WHEN venue LIKE '%Chidambaram%' OR venue LIKE '%Chepauk%' THEN 'MA Chidambaram Stadium, Chennai'
        -- Hyderabad - Rajiv Gandhi
        WHEN venue LIKE '%Rajiv Gandhi%' THEN 'Rajiv Gandhi International Stadium, Hyderabad'
        -- Jaipur
        WHEN venue LIKE '%Sawai Mansingh%' THEN 'Sawai Mansingh Stadium, Jaipur'
        -- Mohali
        WHEN venue LIKE '%Punjab Cricket Association%' OR venue LIKE '%IS Bindra%' THEN 'PCA Stadium, Mohali'
        -- Pune - MCA
        WHEN venue LIKE '%Maharashtra Cricket Association%' THEN 'MCA Stadium, Pune'
        -- Pune - Subrata Roy (old)
        WHEN venue LIKE '%Subrata Roy%' THEN 'MCA Stadium, Pune'
        -- Ahmedabad
        WHEN venue LIKE '%Narendra Modi%' OR venue LIKE '%Sardar Patel%' OR venue LIKE '%Motera%' THEN 'Narendra Modi Stadium, Ahmedabad'
        -- Dharamsala
        WHEN venue LIKE '%Himachal Pradesh%' OR venue LIKE '%Dharamsala%' THEN 'HPCA Stadium, Dharamsala'
        -- Visakhapatnam
        WHEN venue LIKE '%VDCA%' OR venue LIKE '%Visakhapatnam%' OR venue LIKE '%Rajasekhara Reddy%' THEN 'ACA-VDCA Stadium, Visakhapatnam'
        -- Mullanpur/Chandigarh new stadium
        WHEN venue LIKE '%Yadavindra Singh%' OR venue LIKE '%Mullanpur%' THEN 'MIYS Stadium, Mullanpur'
        -- Lucknow
        WHEN venue LIKE '%Ekana%' OR venue LIKE '%Lucknow%' THEN 'Ekana Stadium, Lucknow'
        -- Rajkot
        WHEN venue LIKE '%Saurashtra%' THEN 'Saurashtra Cricket Association Stadium, Rajkot'
        -- Ranchi
        WHEN venue LIKE '%JSCA%' THEN 'JSCA Stadium, Ranchi'
        -- Raipur
        WHEN venue LIKE '%Shaheed Veer Narayan%' THEN 'Shaheed Veer Narayan Singh Stadium, Raipur'
        -- Cuttack
        WHEN venue LIKE '%Barabati%' THEN 'Barabati Stadium, Cuttack'
        -- Guwahati
        WHEN venue LIKE '%Barsapara%' THEN 'Barsapara Stadium, Guwahati'
        -- Kanpur
        WHEN venue LIKE '%Green Park%' THEN 'Green Park, Kanpur'
        -- Indore
        WHEN venue LIKE '%Holkar%' THEN 'Holkar Stadium, Indore'
        -- Nagpur
        WHEN venue LIKE '%Vidarbha%' OR venue LIKE '%Jamtha%' THEN 'VCA Stadium, Nagpur'
        -- UAE venues
        WHEN venue LIKE '%Dubai%' THEN 'Dubai International Cricket Stadium'
        WHEN venue LIKE '%Sharjah%' THEN 'Sharjah Cricket Stadium'
        WHEN venue LIKE '%Sheikh Zayed%' THEN 'Sheikh Zayed Stadium, Abu Dhabi'
        WHEN venue LIKE '%Abu Dhabi%' THEN 'Sheikh Zayed Stadium, Abu Dhabi'
        -- South Africa venues
        WHEN venue LIKE '%Kingsmead%' THEN 'Kingsmead, Durban'
        WHEN venue LIKE '%Newlands%' THEN 'Newlands, Cape Town'
        WHEN venue LIKE '%Wanderers%' THEN 'New Wanderers Stadium, Johannesburg'
        WHEN venue LIKE '%SuperSport%' THEN 'SuperSport Park, Centurion'
        WHEN venue LIKE '%St George%' THEN 'St Georges Park, Port Elizabeth'
        WHEN venue LIKE '%Diamond Oval%' THEN 'De Beers Diamond Oval, Kimberley'
        WHEN venue LIKE '%Buffalo Park%' THEN 'Buffalo Park, East London'
        WHEN venue LIKE '%OUTsurance%' THEN 'OUTsurance Oval, Bloemfontein'
        ELSE venue
    END as venue,
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
