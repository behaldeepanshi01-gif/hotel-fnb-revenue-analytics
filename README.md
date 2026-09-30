# Hotel F&B Revenue Analytics

**How much does food and beverage really add to a hotel's revenue, and where is the upside?**

This project links F&B to how many guests are actually in the hotel each night, so F&B can be measured the way revenue leaders and owners look at it: capture rate, F&B revenue per occupied room, and TRevPAR (total revenue per available room).

![SQL](https://img.shields.io/badge/SQL-SQLite-4479A1?style=flat)
![Python](https://img.shields.io/badge/Python-pandas-3776AB?style=flat)
![Tableau](https://img.shields.io/badge/Tableau-dashboard-E97627?style=flat)

---

## What's real and what's simulated

| Part | Source |
|---|---|
| **Rooms: occupancy, in-house guests, meal plans, room revenue** | **Real.** Rebuilt night by night from 46,000+ actual stays at the City Hotel in the public [Hotel Booking Demand](https://www.sciencedirect.com/science/article/pii/S2352340918315191) dataset (`data/hotels.csv`). |
| **F&B: covers, average check, outside diners, banquets** | **Simulated**, driven by the real guest counts, using the assumptions listed below. |

Because the F&B side is simulated, this project shows **the method**, not a real hotel's result. Every F&B number traces back to an assumption you can read and change in `scripts/generate_data.py`.

**Window:** September 2015 to August 2017 (two full years). July and August 2015 are dropped because the dataset starts with July 2015 arrivals, so guests already in-house are missing and occupancy looks falsely low.

**Rooms available:** the dataset has no capacity field, so the hotel's size is estimated as the busiest night observed (99th percentile): **226 rooms**.

---

## F&B assumptions

| Outlet | Daypart | Share of in-house guests who eat there | Avg check | Outside diners per day (Sun-Thu / Fri-Sat) |
|---|---|---|---|---|
| The Terrace Restaurant | Breakfast | 80% of guests whose rate includes breakfast, 15% of others | $16 (internal value of a package breakfast) | 3 / 5 |
| The Terrace Restaurant | Lunch | 4% | $24 | 22 / 15 |
| The Terrace Restaurant | Dinner | 80% of half/full-board guests, 8% of others | $44 | 16 / 30 |
| Lobby Bar | Evening | 12% | $17 | 14 / 28 |
| In-Room Dining | All day | 3% | $31 | none |
| Banquets & Events | Event | 22% chance of an event on weekdays, 12% on weekends | $55 per head | 30 to 160 attendees |

Outside diners also follow a monthly season curve. Checks vary about 8% day to day. Seed = 42, so results are reproducible.

---

## Results (Year 2: Sep 2016 to Aug 2017)

| KPI | Value |
|---|---|
| Occupancy | 85.7% (real) |
| ADR | $113.78 (real) |
| RevPAR | $97.48 (real) |
| F&B revenue per occupied room | $56.57 |
| **TRevPAR** | **$145.95** |
| F&B share of total revenue | 33.2% |

**What it shows**

1. **F&B lifts revenue per room by about 50%.** RevPAR alone is $97.48. Adding F&B brings total revenue per available room to $145.95. Looking at rooms alone misses a third of the hotel's revenue.
2. **Breakfast is the biggest F&B line (40%)**, because most guests' rates include it. That makes breakfast a packaging and pricing decision as much as a restaurant one.
3. **Dinner only captures about 14% of in-house guests.** Under these assumptions, every extra point of dinner capture is worth about **$62,000 a year**. That's the kind of lever an F&B and revenue team would test.
4. **Outside diners matter most when the hotel is quiet:** 24% of covers on nights under 60% occupancy, vs 12% on nights above 95%. Local marketing should be timed to low-occupancy periods.

---

## How it's built

```
data/hotels.csv            real bookings (public dataset)
   │
   ▼  scripts/generate_data.py
data/rooms_daily.csv       REAL: one row per night (occupancy, guests, room revenue)
data/fnb_daily.csv         SIMULATED: one row per night, outlet and daypart
data/dim_outlet.csv        outlet details
   │
   ▼  sql/01_schema.sql, sql/02_analysis.sql  (run with scripts/run_sql.py)
output/Q1..Q6.csv          query results, ready for Tableau
```

**SQL questions (`sql/02_analysis.sql`)**

| Query | Question |
|---|---|
| Q1 | How does F&B add to rooms? ADR, RevPAR, F&B per occupied room, TRevPAR by year |
| Q2 | What share of in-house guests eat at each outlet (capture rate)? |
| Q3 | Revenue mix by outlet |
| Q4 | When the hotel is full vs quiet, who fills the restaurant? |
| Q5 | Which nights bring the most F&B per guest? |
| Q6 | Monthly trend of occupancy, RevPAR, TRevPAR and F&B per occupied room |

## Run it

```bash
pip install pandas numpy
python scripts/generate_data.py
python scripts/run_sql.py
```

## Limits (said plainly)

- F&B is simulated, so findings 2 to 4 partly reflect the assumptions. The value is the method: linking F&B to real occupancy.
- Room revenue is ADR × nights from the dataset. Currency isn't stated in the source, so treat it as illustrative.
- Rooms available is an estimate.
- The next step would be real outlet POS data (for example Agilysys) joined to PMS occupancy (for example OnQ or OPERA). That's the reconciliation I did by hand at Conrad Washington DC.

---

**Deepanshi Behal** · [Portfolio](https://behaldeepanshi01-gif.github.io) · [LinkedIn](https://linkedin.com/in/bdeepanshi) · [GitHub](https://github.com/behaldeepanshi01-gif)
