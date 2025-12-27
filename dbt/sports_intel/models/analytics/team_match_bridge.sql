WITH matches AS (

    SELECT
        match_id,
        match_date,
        competition_id,
        is_finished,
        home_team_id,
        away_team_id,
        home_goals,
        away_goals,
        result
    FROM {{ ref('fact_matches') }}

)

SELECT
    match_id,
    match_date,
    competition_id,

    home_team_id AS team_id,
    away_team_id AS opponent_id,
    TRUE AS is_home,
    is_finished,

    home_goals AS goals_for,
    away_goals AS goals_against,

    CASE
        WHEN result = 'H' THEN 1
        WHEN result = 'D' THEN 0
        WHEN result = 'A' THEN -1
        ELSE NULL
    END AS outcome

FROM matches

UNION ALL

SELECT
    match_id,
    match_date,
    competition_id,

    away_team_id AS team_id,
    home_team_id AS opponent_id,
    FALSE AS is_home,
    is_finished,

    away_goals AS goals_for,
    home_goals AS goals_against,

    CASE
        WHEN result = 'A' THEN 1
        WHEN result = 'D' THEN 0
        WHEN result = 'H' THEN -1
        ELSE NULL
    END AS outcome

FROM matches
