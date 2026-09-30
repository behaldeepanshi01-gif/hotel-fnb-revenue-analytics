-- Hotel F&B Revenue Analytics: analysis queries
-- Each query answers one question a revenue or F&B leader would ask.

-- Q1. How does F&B add to rooms? KPI summary by year
--     ADR, RevPAR, F&B per occupied room, TRevPAR (rooms + F&B per available room)
WITH f AS (
    SELECT date, SUM(revenue) AS fnb_revenue FROM fnb_daily GROUP BY date
)
SELECT r.fiscal_year,
       ROUND(100.0 * SUM(r.occupied_rooms) / SUM(r.rooms_available), 1)          AS occupancy_pct,
       ROUND(SUM(r.room_revenue) / SUM(r.occupied_rooms), 2)                      AS adr,
       ROUND(SUM(r.room_revenue) / SUM(r.rooms_available), 2)                     AS revpar,
       ROUND(SUM(f.fnb_revenue) / SUM(r.occupied_rooms), 2)                       AS fnb_per_occupied_room,
       ROUND((SUM(r.room_revenue) + SUM(f.fnb_revenue)) / SUM(r.rooms_available), 2) AS trevpar,
       ROUND(100.0 * SUM(f.fnb_revenue) / (SUM(r.room_revenue) + SUM(f.fnb_revenue)), 1) AS fnb_share_pct
FROM rooms_daily r
JOIN f ON f.date = r.date
GROUP BY r.fiscal_year
ORDER BY r.fiscal_year;

-- Q2. Capture rate: what share of in-house guests eat at each outlet?
SELECT f.outlet, f.daypart,
       ROUND(100.0 * SUM(f.hotel_guest_covers) / SUM(r.in_house_guests), 1) AS capture_rate_pct,
       SUM(f.covers)                                                         AS covers,
       ROUND(SUM(f.revenue) / SUM(f.covers), 2)                              AS avg_check,
       ROUND(SUM(f.revenue), 0)                                              AS revenue,
       ROUND(100.0 * SUM(f.outside_covers) / SUM(f.covers), 1)               AS outside_guest_pct
FROM fnb_daily f
JOIN rooms_daily r ON r.date = f.date
WHERE f.outlet <> 'Banquets & Events'
GROUP BY f.outlet, f.daypart
ORDER BY revenue DESC;

-- Q3. Revenue mix by outlet
SELECT outlet,
       ROUND(SUM(revenue), 0) AS revenue,
       ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM fnb_daily), 1) AS share_pct
FROM fnb_daily
GROUP BY outlet
ORDER BY revenue DESC;

-- Q4. When the hotel is full vs quiet: who fills the restaurant?
--     Bucket nights by occupancy and compare F&B per occupied room and outside-guest share
WITH day_f AS (
    SELECT date, SUM(revenue) AS fnb_revenue, SUM(outside_covers) AS outside_cov, SUM(covers) AS cov
    FROM fnb_daily WHERE outlet <> 'Banquets & Events' GROUP BY date
)
SELECT CASE WHEN r.occupancy_pct < 60 THEN '1. Under 60%'
            WHEN r.occupancy_pct < 80 THEN '2. 60-80%'
            WHEN r.occupancy_pct < 95 THEN '3. 80-95%'
            ELSE '4. 95%+' END                                   AS occupancy_band,
       COUNT(*)                                                  AS nights,
       ROUND(SUM(d.fnb_revenue) / SUM(r.occupied_rooms), 2)      AS fnb_per_occupied_room,
       ROUND(100.0 * SUM(d.outside_cov) / SUM(d.cov), 1)         AS outside_guest_pct
FROM rooms_daily r
JOIN day_f d ON d.date = r.date
GROUP BY occupancy_band
ORDER BY occupancy_band;

-- Q5. Day of week: which nights bring the most F&B per guest?
WITH day_f AS (SELECT date, SUM(revenue) AS fnb_revenue FROM fnb_daily GROUP BY date)
SELECT CASE strftime('%w', r.date)
            WHEN '0' THEN '7 Sun' WHEN '1' THEN '1 Mon' WHEN '2' THEN '2 Tue'
            WHEN '3' THEN '3 Wed' WHEN '4' THEN '4 Thu' WHEN '5' THEN '5 Fri'
            ELSE '6 Sat' END                                     AS day_of_week,
       ROUND(AVG(r.occupancy_pct), 1)                            AS avg_occupancy_pct,
       ROUND(SUM(d.fnb_revenue) / SUM(r.occupied_rooms), 2)      AS fnb_per_occupied_room
FROM rooms_daily r
JOIN day_f d ON d.date = r.date
GROUP BY day_of_week
ORDER BY day_of_week;

-- Q6. Monthly trend for Tableau: rooms and F&B side by side
WITH day_f AS (SELECT date, SUM(revenue) AS fnb_revenue FROM fnb_daily GROUP BY date)
SELECT strftime('%Y-%m', r.date)                                 AS month,
       ROUND(100.0 * SUM(r.occupied_rooms) / SUM(r.rooms_available), 1) AS occupancy_pct,
       ROUND(SUM(r.room_revenue) / SUM(r.rooms_available), 2)    AS revpar,
       ROUND((SUM(r.room_revenue) + SUM(d.fnb_revenue)) / SUM(r.rooms_available), 2) AS trevpar,
       ROUND(SUM(d.fnb_revenue) / SUM(r.occupied_rooms), 2)      AS fnb_per_occupied_room
FROM rooms_daily r
JOIN day_f d ON d.date = r.date
GROUP BY month
ORDER BY month;
