
{% macro generate_film_ratings() %}
WITH films_with_ratings AS (
    SELECT
        film_id,
        title,
        release_date,
        price,
        rating,
        user_rating,
        CASE 
            WHEN user_rating >= 4.5 THEN 'Excellent'
            WHEN user_rating >= 4.0 THEN 'GOOD'
            WHEN user_rating >= 3.0 THEN 'Average'
            ELSE 'Poor'
        END as rating_category
    FROM {{ ref('films') }}
),

films_with_actors AS (
    SELECT
        f.film_id,
        f.title,
        STRING_AGG(a.actor_name, ',') AS actors,
        COUNT(a.actor_id) AS actor_count
    FROM {{ ref('films') }} f
    LEFT JOIN {{ ref('film_actors') }} fa ON f.film_id = fa.film_id
    LEFT JOIN {{ ref('actors') }} a ON fa.actor_id = a.actor_id
    GROUP BY f.film_id, f.title
),

actor_ratings AS (
    SELECT
        fa.film_id,
        AVG(f2.user_rating) AS avg_actor_rating
    FROM {{ ref('film_actors') }} fa
    LEFT JOIN {{ ref('film_actors') }} fa2 ON fa.actor_id = fa2.actor_id
    LEFT JOIN {{ ref('films') }} f2 ON fa2.film_id = f2.film_id
    GROUP BY fa.film_id
)

SELECT
    fwr.*,
    fwa.actors,
    COALESCE(fwa.actor_count, 0) AS actor_count,
    COALESCE(
        ar.avg_actor_rating,
        fwr.user_rating
    ) AS avg_actor_rating
FROM
    films_with_ratings fwr
    LEFT JOIN films_with_actors fwa ON fwr.film_id = fwa.film_id
    LEFT JOIN actor_ratings ar ON fwr.film_id = ar.film_id
{% endmacro %}