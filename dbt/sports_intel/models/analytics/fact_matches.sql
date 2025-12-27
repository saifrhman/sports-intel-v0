SELECT
    match_id,
    utc_date,
    CAST(utc_date AS DATE) AS match_date,

    status,
    (status = 'FINISHED') AS is_finished,

    home_team_id,
    away_team_id,
    competition_id,

    home_goals,
    away_goals,
    (home_goals - away_goals) AS goal_diff,

    CASE
        WHEN home_goals > away_goals THEN 'H'
        WHEN home_goals < away_goals THEN 'A'
        WHEN home_goals = away_goals THEN 'D'
        ELSE NULL
    END AS result,

    source

FROM {{ ref('stg_matches') }}
