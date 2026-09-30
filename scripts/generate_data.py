"""
Hotel F&B Revenue Analytics: data generator

What is REAL:      daily occupied rooms, in-house guests, meal plans and room
                   revenue for the City Hotel, rebuilt night by night from the
                   public hotel booking dataset (data/hotels.csv).
What is SIMULATED: everything F&B (covers, average check, banquets, outside
                   guests). Every assumption is listed in ASSUMPTIONS below and
                   in the README, so each number can be explained.

Run:  python scripts/generate_data.py
Out:  data/rooms_daily.csv, data/fnb_daily.csv, data/dim_outlet.csv
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# 1. REAL: rebuild each night in the City Hotel from actual stays
# ---------------------------------------------------------------------------
bk = pd.read_csv(ROOT / "data" / "hotels.csv")
bk = bk[(bk.hotel == "City Hotel") & (bk.is_canceled == 0)].copy()

month_num = {m: i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}
bk["arrival"] = pd.to_datetime(dict(
    year=bk.arrival_date_year,
    month=bk.arrival_date_month.map(month_num),
    day=bk.arrival_date_day_of_month))
bk["nights"] = bk.stays_in_weekend_nights + bk.stays_in_week_nights
bk = bk[bk.nights > 0]
bk["guests"] = bk.adults + bk.children.fillna(0) + bk.babies
bk["package_breakfast"] = bk.meal.isin(["BB", "HB", "FB"]).astype(int)
bk["package_dinner"] = bk.meal.isin(["HB", "FB"]).astype(int)

rows = []
for r in bk.itertuples(index=False):
    for n in range(r.nights):
        rows.append((r.arrival + pd.Timedelta(days=n), r.guests, r.adr,
                     r.package_breakfast * r.guests, r.package_dinner * r.guests))
nights = pd.DataFrame(rows, columns=["date", "guests", "adr",
                                     "breakfast_pkg_guests", "dinner_pkg_guests"])

rooms = nights.groupby("date").agg(
    occupied_rooms=("guests", "size"),
    in_house_guests=("guests", "sum"),
    room_revenue=("adr", "sum"),
    breakfast_pkg_guests=("breakfast_pkg_guests", "sum"),
    dinner_pkg_guests=("dinner_pkg_guests", "sum"),
).reset_index()

# Keep two clean years: Sep 2015 to Aug 2017. The dataset starts with July 2015
# arrivals, so July and August 2015 are missing guests who checked in earlier
# (occupancy looks like 15% to 49%). Dropping them avoids a fake ramp-up.
rooms = rooms[(rooms.date >= "2015-09-01") & (rooms.date <= "2017-08-31")].copy()
rooms["fiscal_year"] = np.where(rooms.date < "2016-09-01", "Year 1 (Sep 15 - Aug 16)",
                                "Year 2 (Sep 16 - Aug 17)")

# Rooms available: the dataset has no capacity field, so we use the busiest
# night observed (99th percentile) as the hotel's room count. Documented.
ROOMS_AVAILABLE = int(np.ceil(rooms.occupied_rooms.quantile(0.99)))
rooms["rooms_available"] = ROOMS_AVAILABLE
rooms["occupancy_pct"] = (rooms.occupied_rooms / ROOMS_AVAILABLE * 100).round(1)
rooms["room_revenue"] = rooms.room_revenue.round(2)

# ---------------------------------------------------------------------------
# 2. SIMULATED: F&B, driven by the real guest counts above
# ---------------------------------------------------------------------------
ASSUMPTIONS = {
    # outlet, daypart: share of in-house guests who eat there (package guests /
    # everyone else), average check ($), outside (non-hotel) covers per day on
    # Sun-Thu / Fri-Sat. Breakfast check is the internal value of a package
    # breakfast, not a menu price.
    ("The Terrace Restaurant", "Breakfast"): dict(capture_pkg=0.80, capture_other=0.15, check=16, outside=(3, 5)),
    ("The Terrace Restaurant", "Lunch"):     dict(capture_pkg=0.00, capture_other=0.04, check=24, outside=(22, 15)),
    ("The Terrace Restaurant", "Dinner"):    dict(capture_pkg=0.80, capture_other=0.08, check=44, outside=(16, 30)),
    ("Lobby Bar", "Evening"):                dict(capture_pkg=0.00, capture_other=0.12, check=17, outside=(14, 28)),
    ("In-Room Dining", "All Day"):           dict(capture_pkg=0.00, capture_other=0.03, check=31, outside=(0, 0)),
}
BANQUET = dict(event_prob_weekday=0.22, event_prob_weekend=0.12,
               attendees=(30, 160), per_head=55)
# Month seasonality for outside diners (1.0 = normal). Lisbon-style city hotel.
OUTSIDE_SEASON = {1: .80, 2: .85, 3: .95, 4: 1.05, 5: 1.10, 6: 1.10,
                  7: 1.05, 8: .90, 9: 1.10, 10: 1.05, 11: .90, 12: 1.00}

fnb = []
for r in rooms.itertuples(index=False):
    weekend = r.date.dayofweek in (4, 5)          # Fri, Sat nights
    season = OUTSIDE_SEASON[r.date.month]
    other_guests = r.in_house_guests - r.breakfast_pkg_guests
    for (outlet, daypart), a in ASSUMPTIONS.items():
        if daypart == "Breakfast":
            hotel_cov = rng.binomial(int(r.breakfast_pkg_guests), a["capture_pkg"]) \
                      + rng.binomial(int(max(other_guests, 0)), a["capture_other"])
        elif daypart == "Dinner":
            non_dinner = r.in_house_guests - r.dinner_pkg_guests
            hotel_cov = rng.binomial(int(r.dinner_pkg_guests), a["capture_pkg"]) \
                      + rng.binomial(int(max(non_dinner, 0)), a["capture_other"])
        else:
            hotel_cov = rng.binomial(int(r.in_house_guests), a["capture_other"])
        base_out = a["outside"][1] if weekend else a["outside"][0]
        outside_cov = int(rng.poisson(base_out * season)) if base_out else 0
        covers = hotel_cov + outside_cov
        check = rng.normal(a["check"], a["check"] * 0.08)
        fnb.append((r.date, outlet, daypart, hotel_cov, outside_cov, covers,
                    round(covers * max(check, a["check"] * 0.6), 2)))

    # Banquets / events
    p = BANQUET["event_prob_weekend"] if weekend else BANQUET["event_prob_weekday"]
    if rng.random() < p:
        att = int(rng.integers(*BANQUET["attendees"]))
        fnb.append((r.date, "Banquets & Events", "Event", 0, att, att,
                    round(att * rng.normal(BANQUET["per_head"], 5), 2)))

fnb = pd.DataFrame(fnb, columns=["date", "outlet", "daypart", "hotel_guest_covers",
                                 "outside_covers", "covers", "revenue"])

dim_outlet = pd.DataFrame({
    "outlet": ["The Terrace Restaurant", "Lobby Bar", "In-Room Dining", "Banquets & Events"],
    "outlet_type": ["Restaurant", "Bar", "In-Room", "Catering"],
    "seats": [140, 60, None, 300],
})

# ---------------------------------------------------------------------------
# 3. Save
# ---------------------------------------------------------------------------
rooms.to_csv(ROOT / "data" / "rooms_daily.csv", index=False, date_format="%Y-%m-%d")
fnb.to_csv(ROOT / "data" / "fnb_daily.csv", index=False, date_format="%Y-%m-%d")
dim_outlet.to_csv(ROOT / "data" / "dim_outlet.csv", index=False)
print(f"rooms_daily: {len(rooms):,} nights | rooms available (est.): {ROOMS_AVAILABLE}")
print(f"fnb_daily:   {len(fnb):,} rows | F&B revenue: ${fnb.revenue.sum():,.0f}")
