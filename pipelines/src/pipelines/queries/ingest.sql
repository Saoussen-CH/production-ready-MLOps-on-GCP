-- Create dataset if it doesn't exist
CREATE SCHEMA IF NOT EXISTS `{{ dataset }}`
  OPTIONS (
    description = 'Chicago Taxi Trips with Production-ready MLops on GCP Template',
    location = '{{ location }}');

-- Create (or replace) table with preprocessed data
DROP TABLE IF EXISTS `{{ dataset }}.{{ table_ }}`;
CREATE TABLE `{{ dataset }}.{{ table_ }}` AS (
-- Determine the latest available data date if use_latest_data is True
WITH latest_data_date AS (
    {% if use_latest_data %}
    SELECT MAX(DATE(trip_start_timestamp)) AS max_date
    FROM `{{ source }}`
    {% else %}
    SELECT DATE('{{ start_timestamp }}') AS max_date
    {% endif %}
)
-- Ingest data between 2 and 3 months ago from the latest available data date
, filtered_data AS (
    SELECT
    *
    FROM `{{ source }}`, latest_data_date
    WHERE
         DATE(trip_start_timestamp) BETWEEN
         DATE_SUB(latest_data_date.max_date, INTERVAL 3 MONTH) AND
         DATE_SUB(latest_data_date.max_date, INTERVAL 2 MONTH)
)
-- Use the average trip_seconds as a replacement for NULL or 0 values
, mean_time AS (
    SELECT CAST(avg(trip_seconds) AS INT64) as avg_trip_seconds
    FROM filtered_data
)

SELECT
    CAST(EXTRACT(DAYOFWEEK FROM trip_start_timestamp) AS FLOAT64) AS dayofweek,
    CAST(EXTRACT(HOUR FROM trip_start_timestamp) AS FLOAT64) AS hourofday,
    ST_DISTANCE(
        ST_GEOGPOINT(pickup_longitude, pickup_latitude),
        ST_GEOGPOINT(dropoff_longitude, dropoff_latitude)) AS trip_distance,
    trip_miles,
    CAST(CASE WHEN trip_seconds IS NULL THEN m.avg_trip_seconds
              WHEN trip_seconds <= 0 THEN m.avg_trip_seconds
              ELSE trip_seconds
              END AS FLOAT64) AS trip_seconds,
    payment_type,
    company,
    {% if label %}
    (fare + tips + tolls + extras) AS `{{ label }}`,
    {% endif %}
FROM filtered_data AS t, mean_time AS m
WHERE
    trip_miles > 0 AND fare > 0 AND fare < 1500
    {% for field in [
        'fare', 'trip_start_timestamp', 'pickup_longitude', 'pickup_latitude',
        'dropoff_longitude', 'dropoff_latitude','payment_type','company' ] %}
        AND `{{ field }}` IS NOT NULL
    {% endfor %}
);
