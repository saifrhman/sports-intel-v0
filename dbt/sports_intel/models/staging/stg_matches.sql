WITH raw AS (

    SELECT
        id         AS raw_id,
        source,
        fetched_at,
        payload
    FROM {{ source('raw', 'matches') }}
    WHERE source = 'football-data.org'

),

exploded_matches AS (

    SELECT
        raw_id,
        source,
        fetched_at,
        jsonb_array_elements(payload->'matches') AS match
    FROM raw

)

SELECT
    raw_id,
    source,
    fetched_at,

    match->>'id'                AS match_id,
    match->>'utcDate'           AS utc_date,
    match->>'status'            AS status,

    match->'homeTeam'->>'id'    AS home_team_id,
    match->'awayTeam'->>'id'    AS away_team_id,

    match->'competition'->>'id' AS competition_id

FROM exploded_matches
-- This is a staging model for football matches data sourced from football-data.org.