"""Yearly data for the person trading a volatile dip strategy."""

IRA_LIMITS = [{"start_year": 1974, "end_year": 1981, "limit": 1500.0},
              {"start_year": 1982, "end_year": 2001, "limit": 2000.0},
              {"start_year": 2002, "end_year": 2004, "limit": 3000.0},
              {"start_year": 2005, "end_year": 2007, "limit": 4000.0},
              {"start_year": 2008, "end_year": 2012, "limit": 5000.0},
              {"start_year": 2013, "end_year": 2018, "limit": 5500.0},
              {"start_year": 2019, "end_year": 2022, "limit": 6000.0},
              {"start_year": 2023, "end_year": 2023, "limit": 6500.0},
              {"start_year": 2024, "end_year": 2025, "limit": 7000.0},
              {"start_year": 2026, "end_year": 2027, "limit": 7500.0},
]

# I have no idea what historic data I should use to get loan interest rates.
#   So, I'm just going to say 5.5% for a collateralized loan rate per year.
LOAN_RATE_YEAR = 0.06

def ira_limit_by_year(year: int) -> float:
    """Given a year (YYYY), returns the IRA limit."""
    if year < 1974:
        print("Year ({}) is before IRA existed...".format(year))
    for ira in IRA_LIMITS:
        if (year <= ira["end_year"]) and (year >= ira["start_year"]):
            return ira["limit"]