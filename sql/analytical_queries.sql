--Average pm2_5 by city
SELECT city, ROUND(AVG(pm2_5), 2) AS avg_pm25
FROM clean_air_weather
GROUP BY city
ORDER BY avg_pm25 DESC;
--2 Do0 Indian cities experience significantly higher air pollution on weekdays compared to weekends due to commuter traffic and industrial activity?
SELECT 
    city,
    CASE 
        WHEN DAYOFWEEK(timestamp) IN (1, 7) THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    ROUND(AVG(pm2_5), 2) AS avg_pm25
FROM clean_air_weather
GROUP BY city, day_type
ORDER BY city, day_type;
--3. Days vs. Night Pollution Trapping
--Question: Do cities experience a major spike in fine particulate matter during nighttime hours compared to daytime hours due to atmospheric boundary layer trapping?
SELECT 
    city,
    CASE 
        WHEN HOUR(timestamp) BETWEEN 6 AND 18 THEN 'Daytime (6 AM - 6 PM)'
        ELSE 'Nighttime (6 PM - 6 AM)'
    END AS time_of_day,
    ROUND(AVG(pm2_5), 2) AS avg_pm25
FROM clean_air_weather
GROUP BY city, time_of_day
ORDER BY city, avg_pm25 DESC;
--4Temperature Extremes
--What are the maximum and minimum recorded temperatures for each city in the dataset?
SELECT 
    city, 
    MAX(temperature_2m) AS max_temp, 
    MIN(temperature_2m) AS min_temp
FROM clean_air_weather
GROUP BY city;
--5Rush Hour vs. Off-Peak Pollution Cycle
--Question: How do daily traffic peaks (morning and evening rush hours) impact PM2.5 concentrations compared to midday or late-night hours?
SELECT 
    city,
    CASE 
        WHEN HOUR(timestamp) BETWEEN 7 AND 10 THEN '1. Morning Rush (7-10 AM)'
        WHEN HOUR(timestamp) BETWEEN 17 AND 21 THEN '2. Evening Rush (5-9 PM)'
        WHEN HOUR(timestamp) BETWEEN 22 AND 23 OR HOUR(timestamp) BETWEEN 0 AND 4 THEN '3. Late Night'
        ELSE '4. Midday / Off-Peak'
    END AS time_period,
    ROUND(AVG(pm2_5), 2) AS avg_pm25,
    ROUND(AVG(temperature_2m), 2) AS avg_temperature,
    ROUND(AVG(relative_humidity_2m), 2) AS avg_humidity,
    ROUND(AVG(nitrogen_dioxide), 2) AS avg_no2
FROM clean_air_weather
GROUP BY city, time_period
ORDER BY city, time_period;
--6City Volatility Ranking (Standard Deviation)
--Which city has the most erratic and unpredictable air quality swings, rather than just a high average?
SELECT 
    city,
    ROUND(AVG(pm10), 2) AS avg_pm10,
    ROUND(STDDEV(pm10), 2) AS pm10_volatility,
    ROUND(AVG(temperature_2m), 2) AS avg_temperature,
    ROUND(STDDEV(temperature_2m), 2) AS temp_volatility,
    ROUND(AVG(relative_humidity_2m), 2) AS avg_humidity,
    ROUND(STDDEV(relative_humidity_2m), 2) AS humidity_volatility,
    ROUND(AVG(nitrogen_dioxide), 2) AS avg_no2,
    ROUND(STDDEV(nitrogen_dioxide), 2) AS no2_volatility
FROM air_quality_project.clean_air_weather
GROUP BY city
ORDER BY pm10_volatility DESC;

--7the exact start and end timestamps for each city directly in your database
SELECT 
    city,
    MIN(timestamp) AS start_time,
    MAX(timestamp) AS end_time,
    COUNT(*) AS total_hours
FROM air_quality_project.clean_air_weather
GROUP BY city;

--8Rainy Hour Count
--How many total hours of recorded precipitation did each city experience over the dataset's timeframe?
SELECT 
    city,
    COUNT(*) AS total_rainy_hours
FROM air_quality_project.clean_air_weather
WHERE precipitation > 0
GROUP BY city
ORDER BY total_rainy_hours DESC;

--9actual heavy downpours versus light mists across these cities, you can run a quick adjustment on the threshold:

SELECT 
    city,
    SUM(CASE WHEN precipitation > 0 AND precipitation <= 1.0 THEN 1 ELSE 0 END) AS light_drizzle_hours,
    SUM(CASE WHEN precipitation > 1.0 THEN 1 ELSE 0 END) AS heavy_rain_hours
FROM air_quality_project.clean_air_weather
GROUP BY city
ORDER BY heavy_rain_hours DESC;
--10 worst air quality day per city
WITH daily_avg AS (
    SELECT 
        city,
        DATE(timestamp) AS reading_date,
        AVG(pm2_5) AS daily_pm25
    FROM air_quality_project.clean_air_weather
    GROUP BY city, DATE(timestamp)
),
ranked_days AS (
    SELECT 
        city,
        reading_date,
        ROUND(daily_pm25, 2) AS daily_pm25,
        ROW_NUMBER() OVER (PARTITION BY city ORDER BY daily_pm25 DESC) AS rnk
    FROM daily_avg
)
SELECT city, reading_date, daily_pm25
FROM ranked_days
WHERE rnk = 1
ORDER BY daily_pm25 DESC;
